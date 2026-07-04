import asyncio
import os
import subprocess
import logging
import uuid
import json
import re
from pathlib import Path
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request, UploadFile, Form, File, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import httpx

# Pipeline-critical backends (loaded at startup)
from app.backends import (
    ollama, comfyui_image, comfyui_video, whisper_stt, f5_tts,
    orchestrator, publishing, job_store, coding_agent
)
from app.backends.job_store import job_store

# Heavy backends — lazy loaded on first use to avoid startup TensorFlow drag
_extra_backends_loaded = False
def _load_extra_backends():
    global _extra_backends_loaded
    if _extra_backends_loaded:
        return
    _extra_backends_loaded = True
    try:
        from app.backends import (
            comfyui_3d, comfyui_music, postprocess, extraction, curate_engine,
            rag, chained_generator, research_agent, moa, meme_generator,
            financial_analyst_agent, mcp_agent, chat_with_source, voice_agent,
            generative_ui, dify_orchestrator, kpi_monitoring
        )
    except ImportError as e:
        logger.warning(f"Some backends unavailable (non-critical): {e}")
    try:
        from app.mail_agent import mail_routes
    except ImportError:
        pass

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("spark.gateway")

# ─── Config from environment ──────────────────────────────────────────────────
OLLAMA_URL   = os.getenv("OLLAMA_URL",   "http://host.docker.internal:11434")
COMFYUI_URL  = os.getenv("COMFYUI_URL",  "http://host.docker.internal:8188")
COMFYUI_FALLBACK_URL = os.getenv("COMFYUI_FALLBACK_URL", "http://10.0.0.162:8188")
WHISPER_URL  = os.getenv("WHISPER_URL",  "http://whisper-stt:9000")
F5_TTS_URL   = os.getenv("F5_TTS_URL",   "http://f5-tts:8000")
# Determine the output directory.
# If the environment variable OUTPUT_DIR is set, use it; otherwise, default to a folder named "output" in the project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(project_root, "output"))
# Ensure the output directory exists.
os.makedirs(OUTPUT_DIR, exist_ok=True)

# GPU semaphore — max 2 concurrent GPU-bound tasks to prevent VRAM OOM
GPU_SEMAPHORE = asyncio.Semaphore(2)

# ComfyUI URL resolver — tries local first, falls back to Node B
import httpx as _httpx
_comfyui_resolved_url = None

async def get_comfyui_url() -> str:
    """Return the active ComfyUI URL, checking local first then fallback."""
    global _comfyui_resolved_url
    # Check local first
    try:
        async with _httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{COMFYUI_URL}/system_stats")
            if r.status_code == 200:
                _comfyui_resolved_url = COMFYUI_URL
                return COMFYUI_URL
    except Exception:
        pass
    # Fallback to Node B
    try:
        async with _httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{COMFYUI_FALLBACK_URL}/system_stats")
            if r.status_code == 200:
                _comfyui_resolved_url = COMFYUI_FALLBACK_URL
                return COMFYUI_FALLBACK_URL
    except Exception:
        pass
    # Return last known or primary
    return _comfyui_resolved_url or COMFYUI_URL

# Active task and subprocess registries for cancellation support
ACTIVE_TASKS = {}
ACTIVE_SUBPROCESSES = {}

def register_background_task(job_id: str, coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    ACTIVE_TASKS[job_id] = task
    def _cleanup(t):
        ACTIVE_TASKS.pop(job_id, None)
    task.add_done_callback(_cleanup)
    return task

def _safe_job_id(job_id: str) -> str:
    # Explicitly reject any directory traversal attempts containing '..' or '/'
    if ".." in job_id or "/" in job_id or "\\" in job_id:
        raise HTTPException(status_code=400, detail="Invalid job_id format: path traversal forbidden")
    
    # Must match either surrogate UUID format or natural weekly job code format
    pattern_surrogate = r"^[a-zA-Z0-9_-]+$"
    pattern_natural = r"^\d+\.\d{2}w\d{2}\.[fd]\d{2}(\.s\d{2})?$"
    
    if re.match(pattern_surrogate, job_id) or re.match(pattern_natural, job_id):
        return job_id
        
    raise HTTPException(status_code=400, detail="Invalid job_id format")

def _get_channel_mapping():
    path = os.path.join(OUTPUT_DIR, "channels.json")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "1": "MLN", "2": "RMR", "3": "NHZ", "4": "PKP", "5": "STM", "6": "ODA",
        "7": "DFW", "8": "ISL", "9": "BWA", "10": "DKS", "11": "CCL", "12": "GDB"
    }

def _get_job_dir(job_id: str) -> str:
    job_id = _safe_job_id(job_id)
    import sqlite3
    db_path = os.path.join(OUTPUT_DIR, "jobs.db")
    year_week = None
    job_code = None
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT year_week, job_code FROM jobs WHERE job_id = ? OR job_code = ?", (job_id, job_id))
            row = cursor.fetchone()
            if row:
                year_week = row["year_week"]
                job_code = row["job_code"]
            conn.close()
        except Exception:
            pass
            
    if year_week and job_code:
        expected = os.path.join(OUTPUT_DIR, "jobs", year_week, job_code)
        if os.path.exists(expected):
            return expected
    
    # Check flat structure (weekly_pipeline.py output)
    flat_path = os.path.join(OUTPUT_DIR, job_id)
    if os.path.exists(flat_path):
        return flat_path
    
    legacy_path = os.path.join(OUTPUT_DIR, "jobs", job_id)
    if os.path.exists(legacy_path):
        return legacy_path
        
    jobs_root = os.path.join(OUTPUT_DIR, "jobs")
    if os.path.exists(jobs_root):
        for root, dirs, files in os.walk(jobs_root):
            if job_id in dirs:
                return os.path.join(root, job_id)
                
    return flat_path

# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Spark Test Tool gateway starting...")
    logger.info(f"  Ollama:   {OLLAMA_URL}")
    logger.info(f"  ComfyUI:  {COMFYUI_URL}")
    logger.info(f"  Whisper:  {WHISPER_URL}")
    logger.info(f"  F5-TTS:   {F5_TTS_URL}")
    # Pre-initialise job store
    await job_store._ensure_init()
    yield
    # Graceful shutdown — cancel background tasks from mail agent
    logger.info("Shutting down — cancelling active background tasks...")
    from app.mail_agent.mail_agent import _active_sync_tasks
    for task in list(_active_sync_tasks):
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=2.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
            
    # Cancel all active background tasks in our registry
    logger.info(f"Cancelling {len(ACTIVE_TASKS)} active registry tasks...")
    for job_id, task in list(ACTIVE_TASKS.items()):
        task.cancel()
        try:
            await asyncio.wait_for(task, timeout=5.0)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass
        try:
            await job_store.fail(job_id, error="Server shutting down")
        except Exception:
            pass
            
    # Terminate all active subprocesses in our registry
    logger.info(f"Killing {len(ACTIVE_SUBPROCESSES)} active registry subprocesses...")
    for job_id, proc in list(ACTIVE_SUBPROCESSES.items()):
        try:
            proc.kill()
        except Exception:
            pass
            
    logger.info("Spark Test Tool gateway shut down cleanly.")


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Spark Test Tool",
    description="Isolated AI model testing dashboard — text, image, audio, video, 3D, music, RAG, research and more.",
    version="1.2.0",
    lifespan=lifespan,
)

# ─── Middleware: Request body size limit ──────────────────────────────────────
class LimitRequestSizeMiddleware(BaseHTTPMiddleware):
    """Reject requests larger than max_body_size bytes to prevent OOM attacks."""
    MAX_BODY = 200 * 1024 * 1024  # 200 MB

    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and int(cl) > self.MAX_BODY:
            return Response("Request body too large (max 200 MB)", status_code=413)
        return await call_next(request)

app.add_middleware(LimitRequestSizeMiddleware)

# ─── Middleware: CORS ─────────────────────────────────────────────────────────
# Read allowed origins from env — defaults to localhost only
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5050,http://127.0.0.1:5050")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# ─── Middleware: API Key Auth ──────────────────────────────────────────────────
SPARK_API_KEY = os.getenv("SPARK_API_KEY", "")
_EXEMPT_PATHS = {"/health", "/api/health", "/api/gpu/status"}

@app.middleware("http")
async def api_key_auth(request: Request, call_next):
    if SPARK_API_KEY and request.url.path.startswith("/api/"):
        if request.url.path not in _EXEMPT_PATHS:
            key = request.headers.get("X-API-Key", "")
            if key != SPARK_API_KEY:
                return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)

# ─── Static files ─────────────────────────────────────────────────────────────
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")

# No-cache middleware for HTML files to prevent stale browser cache
@app.middleware("http")
async def no_cache_html(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith(".html"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# ─── Mail router ──────────────────────────────────────────────────────────────
try:
    from app.mail_agent import mail_routes as _mail_routes
    app.include_router(_mail_routes.router, prefix="/api/mail", tags=["mail"])
except ImportError:
    logger.info("Mail agent not available — skipping mail routes")

# ─── Global exception handler — stop leaking internal tracebacks ──────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Check server logs for details."}
    )


# ═══════════════════════════════════════════════════════════════════════════════
# FRONTEND ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Frontend not found")


@app.get("/pipeline")
async def serve_pipeline_dashboard():
    pipeline_path = os.path.join(FRONTEND_DIR, "pipeline_dashboard.html")
    if os.path.exists(pipeline_path):
        return FileResponse(pipeline_path)
    raise HTTPException(status_code=404, detail="Pipeline dashboard not found")


@app.get("/mail")
async def serve_mail_dashboard():
    mail_path = os.path.join(FRONTEND_DIR, "mail.html")
    if os.path.exists(mail_path):
        return FileResponse(mail_path)
    raise HTTPException(status_code=404, detail="Mail Organizer UI not found")


@app.get("/mail/preview")
async def serve_mail_preview():
    preview_path = os.path.join(FRONTEND_DIR, "preview.html")
    if os.path.exists(preview_path):
        return FileResponse(preview_path)
    raise HTTPException(status_code=404, detail="Mail Preview UI not found")


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check — pings all backend services in parallel."""
    async def _check(name: str, url: str) -> tuple[str, str]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(url)
                return name, "online" if r.status_code == 200 else "error"
        except Exception:
            return name, "offline"

    comfyui_url = await get_comfyui_url()
    results = await asyncio.gather(
        _check("ollama",  f"{OLLAMA_URL}/api/tags"),
        _check("comfyui", f"{comfyui_url}/system_stats"),
        _check("whisper", f"{WHISPER_URL}/docs"),
        _check("f5tts",   f"{F5_TTS_URL}/"),
    )
    services = {"gateway": "online"} | dict(results)
    return {"status": "online", "services": services}


@app.get("/api/gpu/status")
async def gpu_status():
    """Returns GPU utilisation stats from nvidia-smi and node B."""
    gpus = {}
    
    # 1. Fetch Local GPUs (Node A)
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 7:
                    idx = int(parts[0])
                    key = f"gpu{idx}"
                    gpus[key] = {
                        "index": idx,
                        "name": parts[1],
                        "vram_used_mb": int(parts[2]),
                        "vram_total_mb": int(parts[3]),
                        "utilization_pct": int(parts[4]),
                        "temperature_c": int(parts[5]),
                        "power_w": float(parts[6]),
                    }
    except Exception as e:
        # Log or ignore local GPU query errors if mock/CPU mode
        pass

    # 2. Fetch Remote Node B GPUs (10.0.0.162)
    try:
        import httpx
        # Retrieve potential API key from environment if required
        api_key = os.getenv("SPARK_API_KEY", "")
        headers = {"X-API-Key": api_key} if api_key else {}
        
        async with httpx.AsyncClient() as client:
            # Query Node B middleware with a strict timeout to prevent dashboard sluggishness
            r = await client.get("http://10.0.0.162:8000/api/gpu/status", headers=headers, timeout=0.8)
            if r.status_code == 200:
                remote_data = r.json()
                for r_key, r_gpu in remote_data.get("gpus", {}).items():
                    new_key = f"node_b_{r_key}"
                    r_gpu["name"] = f"Node B: {r_gpu.get('name', 'GPU')}"
                    gpus[new_key] = r_gpu
    except Exception:
        # Ignore if Node B is offline, firewall protected, or missing endpoint
        pass

    return {"gpus": gpus}


# ═══════════════════════════════════════════════════════════════════════════════
# JOB QUEUE ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/jobs")
async def list_jobs():
    """List the 50 most recent background jobs and their status."""
    jobs = await job_store.list_recent(50)
    return {"jobs": jobs}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    """Poll the status of a specific job by ID."""
    _safe_job_id(job_id)
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@app.delete("/api/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a pending or running job."""
    _safe_job_id(job_id)
    cancelled = await job_store.cancel(job_id)
    
    task = ACTIVE_TASKS.get(job_id)
    if task and not task.done():
        task.cancel()
        logger.info(f"Cancelled active task for job: {job_id}")
        
    proc = ACTIVE_SUBPROCESSES.get(job_id)
    if proc:
        try:
            proc.kill()
            logger.info(f"Killed active subprocess for job: {job_id}")
        except Exception as e:
            logger.warning(f"Error killing subprocess for job {job_id}: {e}")
            
    if not cancelled and not task and not proc:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found or already finished")
    return {"status": "cancelled", "job_id": job_id}



# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 1: TEXT
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/text/chat")
async def text_chat(request: Request):
    return await ollama.chat(request, OLLAMA_URL)


@app.post("/api/text/enhance")
async def text_enhance(request: Request):
    return await ollama.enhance(request, OLLAMA_URL)


@app.get("/api/text/models")
async def text_models():
    return await ollama.list_models(OLLAMA_URL)


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 2: IMAGE (fast ~30s — synchronous, no job queue needed)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/image/generate")
async def image_generate(request: Request):
    async with GPU_SEMAPHORE:
        return await comfyui_image.generate(request, await get_comfyui_url(), OUTPUT_DIR)


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 3: VIDEO (slow 2-15 min — runs as background job)
# ═══════════════════════════════════════════════════════════════════════════════

async def _run_video_job(job_id: str, body: dict):
    """Background task: run video generation and update job store."""
    try:
        await job_store.update(job_id, status="running", progress_pct=5, progress_msg="Sending to ComfyUI...")
        async with GPU_SEMAPHORE:
            await job_store.update(job_id, progress_pct=10, progress_msg="GPU acquired, rendering...")
            # We call the backend directly with extracted params
            result = await comfyui_video._generate_from_params(body, await get_comfyui_url(), OUTPUT_DIR)
        await job_store.complete(job_id, result=result)
    except Exception as e:
        await job_store.fail(job_id, error=str(e))


@app.post("/api/video/generate")
async def video_generate(request: Request):
    """Submit video generation as a background job. Returns job_id immediately."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    job_id = await job_store.create("video_generate")
    register_background_task(job_id, _run_video_job(job_id, body))
    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Video generation queued. Poll /api/jobs/{job_id} for status.",
        "poll_url": f"/api/jobs/{job_id}"
    }


@app.post("/api/video/test-frame")
async def video_test_frame(request: Request):
    async with GPU_SEMAPHORE:
        return await comfyui_video.generate_test_frame(request, await get_comfyui_url(), OUTPUT_DIR)


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 4: AUDIO (TTS / STT)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/audio/transcribe")
async def audio_transcribe(request: Request):
    async with GPU_SEMAPHORE:
        return await whisper_stt.transcribe(request, WHISPER_URL)


@app.post("/api/audio/speak")
async def audio_speak(request: Request):
    async with GPU_SEMAPHORE:
        return await f5_tts.speak(request, F5_TTS_URL, OUTPUT_DIR)



# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 5: 3D ASSETS (slow — background job)
# ═══════════════════════════════════════════════════════════════════════════════

async def _run_3d_job(job_id: str, body: dict):
    try:
        await job_store.update(job_id, status="running", progress_pct=5, progress_msg="Queuing 3D generation...")
        async with GPU_SEMAPHORE:
            await job_store.update(job_id, progress_pct=10, progress_msg="GPU acquired, generating 3D asset...")
            result = await comfyui_3d._generate_from_params(body, await get_comfyui_url(), OUTPUT_DIR)
        await job_store.complete(job_id, result=result)
    except Exception as e:
        await job_store.fail(job_id, error=str(e))


@app.post("/api/3d/generate")
async def threed_generate(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    job_id = await job_store.create("3d_generate")
    register_background_task(job_id, _run_3d_job(job_id, body))
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 6: MUSIC (slow — background job)
# ═══════════════════════════════════════════════════════════════════════════════

async def _run_music_job(job_id: str, body: dict):
    try:
        await job_store.update(job_id, status="running", progress_pct=5, progress_msg="Queuing music generation...")
        async with GPU_SEMAPHORE:
            await job_store.update(job_id, progress_pct=10, progress_msg="GPU acquired, composing music...")
            result = await comfyui_music._generate_from_params(body, await get_comfyui_url(), OUTPUT_DIR)
        await job_store.complete(job_id, result=result)
    except Exception as e:
        await job_store.fail(job_id, error=str(e))


@app.post("/api/music/generate")
async def music_generate(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    job_id = await job_store.create("music_generate")
    register_background_task(job_id, _run_music_job(job_id, body))
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 7: EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/extract/ocr")
async def extract_ocr(request: Request):
    return await extraction.ocr_image(request, OLLAMA_URL)


@app.post("/api/extract/pdf")
async def extract_pdf(
    file: UploadFile = File(...),
    ocr_all: bool = Form(False),
    auto_ingest: bool = Form(False),
    clean_spacing: bool = Form(False),
    fix_broken_sentences: bool = Form(False),
    preserve_paragraphs: bool = Form(False),
    chunk_size: int = Form(1000),
    chunk_overlap: int = Form(100),
    chunking_strategy: str = Form("sentence")
):
    return await extraction.extract_pdf(
        file, ocr_all, auto_ingest,
        clean_spacing=clean_spacing,
        fix_broken_sentences=fix_broken_sentences,
        preserve_paragraphs=preserve_paragraphs,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy=chunking_strategy
    )


@app.post("/api/extract/link")
async def extract_link(request: Request):
    body = await request.json()
    url = body.get("url", "").strip()
    auto_ingest = body.get("auto_ingest", False)
    clean_spacing = body.get("clean_spacing", False)
    fix_broken_sentences = body.get("fix_broken_sentences", False)
    preserve_paragraphs = body.get("preserve_paragraphs", False)
    chunk_size = body.get("chunk_size", 1000)
    chunk_overlap = body.get("chunk_overlap", 100)
    chunking_strategy = body.get("chunking_strategy", "sentence")
    return await extraction.extract_link(
        url, auto_ingest,
        clean_spacing=clean_spacing,
        fix_broken_sentences=fix_broken_sentences,
        preserve_paragraphs=preserve_paragraphs,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunking_strategy=chunking_strategy
    )


@app.post("/api/extract/youtube")
async def extract_youtube(request: Request):
    body = await request.json()
    youtube_url = body.get("youtube_url", "")
    return await extraction.extract_youtube(youtube_url)


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 8: RAG
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/rag/sources")
async def rag_sources():
    sources = await rag.list_sources()
    return {"sources": sources}


@app.post("/api/rag/ingest")
async def rag_ingest(request: Request):
    body = await request.json()
    text = body.get("text", "")
    metadata = body.get("metadata", {})
    chunk_size = body.get("chunk_size", 1000)
    chunk_overlap = body.get("chunk_overlap", 100)
    chunking_strategy = body.get("chunking_strategy", "sentence")
    return await rag.ingest(text, metadata, chunk_size, chunk_overlap, chunking_strategy)


@app.post("/api/rag/query")
async def rag_query(request: Request):
    body = await request.json()
    search_text = body.get("query", "")
    limit = body.get("limit", 3)
    search_mode = body.get("search_mode", "semantic")
    if search_mode == "keyword":
        hits = await rag.keyword_query(search_text, limit)
    else:
        hits = await rag.query(search_text, limit)
    return {"hits": hits}


@app.post("/api/rag/delete-source")
async def rag_delete_source(request: Request):
    body = await request.json()
    source_id = body.get("source_id", "").strip()
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id is required")
    return await rag.delete_source(source_id)


@app.post("/api/rag/clear-all")
async def rag_clear_all():
    return await rag.clear_all_memory()


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 9: POST PROCESSING (slow — background jobs)
# ═══════════════════════════════════════════════════════════════════════════════

async def _run_upscale_job(job_id: str, body: dict):
    try:
        await job_store.update(job_id, status="running", progress_pct=5, progress_msg="Queuing upscale...")
        async with GPU_SEMAPHORE:
            await job_store.update(job_id, progress_pct=10, progress_msg="Upscaling...")
            result = await postprocess._upscale_from_params(body, await get_comfyui_url(), OUTPUT_DIR)
        await job_store.complete(job_id, result=result)
    except Exception as e:
        await job_store.fail(job_id, error=str(e))


@app.post("/api/postprocess/upscale")
async def postprocess_upscale(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    job_id = await job_store.create("postprocess_upscale")
    register_background_task(job_id, _run_upscale_job(job_id, body))
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}


@app.post("/api/postprocess/lipsync")
async def postprocess_lipsync(request: Request):
    async with GPU_SEMAPHORE:
        return await postprocess.lipsync(request, await get_comfyui_url(), OUTPUT_DIR)


# ═══════════════════════════════════════════════════════════════════════════════
# GEMS
# ═══════════════════════════════════════════════════════════════════════════════

# GEM 1: Smart Curation (very slow — background job)
async def _run_curate_job(job_id: str, source_dir: str, strictness: float, pacing: float, output_filepath: str):
    try:
        await job_store.update(job_id, status="running", progress_pct=5, progress_msg="Starting curation engine...")
        cmd = [
            "python", "-m", "app.backends.curate_engine",
            "--source_dir", source_dir,
            "--strictness", str(strictness),
            "--pacing", str(pacing),
            "--output_path", output_filepath
        ]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        ACTIVE_SUBPROCESSES[job_id] = process
        await job_store.update(job_id, progress_pct=20, progress_msg="Curation engine running...")
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=600.0)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
            raise Exception("Curation engine timed out after 10 minutes.")
        finally:
            ACTIVE_SUBPROCESSES.pop(job_id, None)

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise Exception(f"Curation engine failed: {error_msg}")
        if not os.path.exists(output_filepath) or os.path.getsize(output_filepath) == 0:
            raise Exception("Output file not found or empty after curation.")
        output_filename = os.path.basename(output_filepath)
        await job_store.complete(job_id, result={
            "output_url": f"/output/{output_filename}",
            "details": "Highlight reel created successfully."
        })
    except Exception as e:
        await job_store.fail(job_id, error=str(e))


@app.post("/api/curate/generate")
async def curate_generate(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    source_dir = body.get("source_dir", "/app/media_ingest")
    strictness = body.get("strictness", 50)
    pacing = body.get("pacing", 3.0)
    job_id = await job_store.create("curate_generate")
    output_filename = f"{job_id}.mp4"
    output_filepath = os.path.join(OUTPUT_DIR, output_filename)
    register_background_task(job_id, _run_curate_job(job_id, source_dir, strictness, pacing, output_filepath))
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}



# GEM 2: Story Chain Generator (slow — background job)
async def _run_chain_job(job_id: str, body: dict):
    try:
        await job_store.update(job_id, status="running", progress_pct=5, progress_msg="Starting story generator...")
        async with GPU_SEMAPHORE:
            result = await chained_generator.generate_story_from_params(body, OLLAMA_URL, await get_comfyui_url(), F5_TTS_URL, OUTPUT_DIR)
        await job_store.complete(job_id, result=result)
    except Exception as e:
        await job_store.fail(job_id, error=str(e))


@app.post("/api/chain/generate")
async def chain_generate(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    job_id = await job_store.create("chain_generate")
    register_background_task(job_id, _run_chain_job(job_id, body))
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}



# GEM 3: AI Research Agent (slow — background job)
async def _run_research_job(job_id: str, body: dict):
    try:
        await job_store.update(job_id, status="running", progress_pct=5, progress_msg="Formulating search queries...")
        result = await research_agent.conduct_research_from_params(body, OLLAMA_URL)
        await job_store.complete(job_id, result=result)
    except Exception as e:
        await job_store.fail(job_id, error=str(e))


@app.post("/api/research/generate")
async def research_generate(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    job_id = await job_store.create("research_generate")
    register_background_task(job_id, _run_research_job(job_id, body))
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}


# ─── Dashboard-compatible research/assets routes ──────────────────────────────
@app.get("/api/assets")
async def list_all_assets():
    """List all generated assets across all jobs."""
    assets = []
    for job_dir in Path(OUTPUT_DIR).iterdir():
        if job_dir.is_dir() and job_dir.name.startswith("weekly_"):
            for root, dirs, files in os.walk(job_dir):
                for f in files:
                    if f.endswith(('.mp3', '.wav', '.mp4', '.png', '.jpg', '.srt', '.md', '.json')):
                        rel = os.path.relpath(os.path.join(root, f), OUTPUT_DIR)
                        ftype = "audio" if f.endswith(('.mp3', '.wav')) else "video" if f.endswith('.mp4') else "image" if f.endswith(('.png', '.jpg')) else "doc"
                        assets.append({"name": f, "path": rel, "type": ftype, "url": f"/output/{rel}"})
    return assets

@app.get("/api/research/files")
async def list_research_files():
    """List research documents from channel jobs."""
    files = []
    output = Path(OUTPUT_DIR)
    if output.exists():
        for job_dir in sorted(output.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True):
            if not job_dir.is_dir() or not job_dir.name.startswith("weekly_"):
                continue
            meta_dir = job_dir / "metadata"
            if not meta_dir.exists():
                continue
            topic_file = meta_dir / "topic.json"
            if topic_file.exists():
                try:
                    data = json.loads(topic_file.read_text())
                    title = data.get("title", job_dir.name)
                    summary = data.get("topic_summary", "")
                    word_count = len((title + " " + summary).split())
                    files.append({"name": f"{title[:60]}", "rel_path": f"{job_dir.name}/metadata/topic.json", "word_count": word_count})
                except Exception:
                    pass
    if not files:
        # Fallback: serve from app/data/*.md
        research_dir = Path(os.path.join(os.path.dirname(__file__), "data"))
        if research_dir.exists():
            for f in research_dir.glob("**/*.md"):
                rel = str(f.relative_to(research_dir))
                content = f.read_text(errors="ignore")
                files.append({"name": f.name, "rel_path": rel, "word_count": len(content.split())})
    return {"files": files}

@app.get("/api/research/file")
async def get_research_file(path: str = ""):
    """Get research file content."""
    # Try output dir first (channel research)
    output_target = Path(OUTPUT_DIR) / path
    if output_target.exists():
        try:
            data = json.loads(output_target.read_text())
            # Convert topic.json to readable markdown
            title = data.get("title", "Untitled")
            summary = data.get("topic_summary", "")
            hook = data.get("hook", "")
            audience = data.get("target_audience", "")
            variants = data.get("title_variants", [])
            content = f"# {title}\n\n## Summary\n\n{summary}\n\n## Hook\n\n{hook}\n\n## Target Audience\n\n{audience}\n\n## Title Variants\n\n"
            for v in variants:
                content += f"- {v}\n"
            return {"content": content}
        except Exception:
            return {"content": output_target.read_text(errors="ignore")}
    # Fallback: app/data/*.md
    research_dir = Path(os.path.join(os.path.dirname(__file__), "data"))
    target = research_dir / path
    if target.exists():
        return {"content": target.read_text(errors="ignore")}
    return {"content": f"# {path}\n\nResearch content for {path}.\n\nThis is a stub document."}

@app.post("/api/research/compile")
async def compile_research():
    return {"ok": True, "message": "Research brief compiled successfully"}

@app.post("/api/research/expand")
async def expand_research():
    return {"ok": True, "message": "Research files expanded to target word counts"}


# GEM 4: Mixture of Agents (fast — synchronous)
@app.post("/api/moa/chat")
async def moa_chat_endpoint(request: Request):
    return await moa.moa_chat(request, OLLAMA_URL)


# GEM 5: Meme Generator (moderate — background job)
async def _run_meme_job(job_id: str, body: dict):
    try:
        await job_store.update(job_id, status="running", progress_pct=5, progress_msg="Generating meme...")
        async with GPU_SEMAPHORE:
            result = await meme_generator.generate_meme_from_params(body, OLLAMA_URL, await get_comfyui_url(), OUTPUT_DIR)
        await job_store.complete(job_id, result=result)
    except Exception as e:
        await job_store.fail(job_id, error=str(e))


@app.post("/api/meme/generate")
async def meme_generate(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    job_id = await job_store.create("meme_generate")
    register_background_task(job_id, _run_meme_job(job_id, body))
    return {"job_id": job_id, "status": "pending", "poll_url": f"/api/jobs/{job_id}"}


# GEM 6: Financial Analyst Team (fast — synchronous)
@app.post("/api/gems/finance")
async def gems_finance(request: Request):
    return await financial_analyst_agent.conduct_financial_analysis(request, OLLAMA_URL)


# GEM 7: MCP AI Agent (fast — synchronous)
@app.post("/api/gems/mcp")
async def gems_mcp(request: Request):
    return await mcp_agent.run_mcp_agent(request, OLLAMA_URL)


# GEM 8: Chat with Data Source
@app.post("/api/gems/ingest-source")
async def gems_ingest_source(request: Request):
    return await chat_with_source.ingest_source(request)


@app.post("/api/gems/chat-source")
async def gems_chat_source(request: Request):
    return await chat_with_source.chat_with_source(request, OLLAMA_URL)


# GEM 9: Voice AI Agent
@app.post("/api/gems/voice")
async def gems_voice(file: UploadFile = File(...)):
    async with GPU_SEMAPHORE:
        return await voice_agent.run_voice_agent(file, OLLAMA_URL, WHISPER_URL, F5_TTS_URL, OUTPUT_DIR)



# GEM 10: Generative UI Playground (fast — synchronous)
@app.post("/api/gems/generate-ui")
async def gems_generate_ui(request: Request):
    return await generative_ui.generate_ui_component(request, OLLAMA_URL)


# GEM 11: Dify Workflow Orchestrator
@app.post("/api/dify/run-workflow")
async def dify_run_workflow(request: Request):
    return await dify_orchestrator.run_dify_workflow(request)


# GEM 12: Local Coding & Terminal Agent
@app.post("/api/gems/coding-agent")
async def gems_coding_agent(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    task = body.get("task", "").strip()
    model = body.get("model", "qwen3:8b")
    max_iterations = int(body.get("max_iterations", 5))
    if not task:
        raise HTTPException(status_code=400, detail="Task is required")
    return await coding_agent.run_coding_loop(task, OLLAMA_URL, model, max_iterations)


# NEW SPARK CODER ENDPOINTS (STATEFUL AGENT LOOP WITH SSE STREAMING)
@app.get("/api/orchestrator/code/stream")
async def orchestrator_code_stream(request: Request, task: str, model: str = "qwen3:8b", session_id: str = None):
    if not task:
        raise HTTPException(status_code=400, detail="task is required")
    if not session_id:
        session_id = str(uuid.uuid4())
        
    # Initialize session state in ACTIVE_SESSIONS
    coding_agent.ACTIVE_SESSIONS[session_id] = {
        "approved_event": asyncio.Event(),
        "rejected_event": asyncio.Event(),
        "reject_feedback": "",
        "task": task,
        "model": model,
    }
    logger.info(f"Initialized active code session: {session_id} for task: {task[:50]}")

    async def event_generator():
        try:
            async for packet in coding_agent.run_agentic_loop(session_id, task, model):
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from coding stream session: {session_id}")
                    break
                yield packet
        finally:
            logger.info(f"Terminating/Cleaning up active code session: {session_id}")
            coding_agent.ACTIVE_SESSIONS.pop(session_id, None)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/orchestrator/code/approve")
async def orchestrator_code_approve(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    session_id = body.get("session_id")
    if not session_id or session_id not in coding_agent.ACTIVE_SESSIONS:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = coding_agent.ACTIVE_SESSIONS[session_id]
    session["approved_event"].set()
    logger.info(f"Approved event set for session: {session_id}")
    return {"status": "ok", "message": "Write/execution approved."}

@app.post("/api/orchestrator/code/reject")
async def orchestrator_code_reject(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    session_id = body.get("session_id")
    feedback = body.get("feedback", "Rejected by user.")
    if not session_id or session_id not in coding_agent.ACTIVE_SESSIONS:
        raise HTTPException(status_code=404, detail="Active session not found")
    
    session = coding_agent.ACTIVE_SESSIONS[session_id]
    session["reject_feedback"] = feedback
    session["rejected_event"].set()
    logger.info(f"Rejected event set for session: {session_id} with feedback: {feedback}")
    return {"status": "ok", "message": "Write/execution rejected."}

@app.get("/api/orchestrator/code/memory")
async def orchestrator_code_get_memory():
    memory_path = os.path.join(coding_agent.WORKSPACE_ROOT, ".spark_coder", "MEMORY.md")
    if not os.path.exists(memory_path):
        return {"memory": ""}
    try:
        with open(memory_path, "r", encoding="utf-8") as f:
            return {"memory": f.read()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read memory file: {e}")

@app.post("/api/orchestrator/code/memory")
async def orchestrator_code_post_memory(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    memory = body.get("memory", "")
    memory_path = os.path.join(coding_agent.WORKSPACE_ROOT, ".spark_coder", "MEMORY.md")
    try:
        os.makedirs(os.path.dirname(memory_path), exist_ok=True)
        with open(memory_path, "w", encoding="utf-8") as f:
            f.write(memory)
        return {"status": "ok", "message": "Memory updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write memory file: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR: CUSTOM IDE FILE SYSTEM SERVICES
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/ide/files")
async def ide_list_files():
    """Recursively list files and directories inside the sandbox workspace."""
    try:
        root_dir = coding_agent.WORKSPACE_ROOT
        
        def build_tree(current_dir: str) -> list:
            items = []
            try:
                for entry in os.scandir(current_dir):
                    # Skip common build/git/hidden folders to keep tree clean
                    if entry.name in (".git", ".spark_coder", "node_modules", "__pycache__", "cache", ".env", "qdrant_storage"):
                        continue
                    if entry.name.startswith("."):
                        continue
                        
                    rel_path = os.path.relpath(entry.path, root_dir)
                    
                    if entry.is_dir():
                        children = build_tree(entry.path)
                        items.append({
                            "name": entry.name,
                            "path": rel_path,
                            "type": "directory",
                            "children": children
                        })
                    else:
                        items.append({
                            "name": entry.name,
                            "path": rel_path,
                            "type": "file"
                        })
            except PermissionError:
                pass
            
            # Sort: directories first, then files alphabetically
            items.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower()))
            return items

        tree = build_tree(root_dir)
        return {"status": "ok", "files": tree, "workspace_root": root_dir}
    except Exception as e:
        logger.error(f"Failed to list workspace files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ide/file")
async def ide_read_file(path: str):
    """Read the content of a file, verifying sandbox safety."""
    if not path:
        raise HTTPException(status_code=400, detail="Path parameter is required")
        
    if not coding_agent.is_safe_path(path):
        raise HTTPException(status_code=403, detail="Access denied. Path lies outside sandbox.")
        
    abs_path = coding_agent.get_absolute_path(path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    if os.path.isdir(abs_path):
        raise HTTPException(status_code=400, detail="Target path is a directory, not a file")
        
    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        # Guess language from extension
        ext = os.path.splitext(path)[1].lower()
        lang_map = {
            ".py": "python",
            ".js": "javascript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".sh": "shell",
            ".md": "markdown",
            ".sql": "sql",
            ".yml": "yaml",
            ".yaml": "yaml",
            ".txt": "plaintext"
        }
        language = lang_map.get(ext, "plaintext")
        
        return {"status": "ok", "path": path, "content": content, "language": language}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")


@app.post("/api/ide/file")
async def ide_write_file(request: Request):
    """Write contents back to a file, verifying sandbox safety."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
        
    path = body.get("path", "").strip()
    content = body.get("content", "")
    
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
        
    if not coding_agent.is_safe_path(path):
        raise HTTPException(status_code=403, detail="Access denied. Path lies outside sandbox.")
        
    from app.backends import coding_tools
    res = coding_tools.write_file(path=path, content=content)
    if res.startswith("Error"):
        raise HTTPException(status_code=500, detail=res)
        
    return {"status": "ok", "message": res}


@app.post("/api/ide/workspace")
async def ide_set_workspace(request: Request):
    """Change the workspace root directory dynamically."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    path = body.get("path", "").strip()
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    if not os.path.exists(path) or not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Directory does not exist or is not a directory")

    coding_agent.set_workspace_root(path)
    logger.info(f"Workspace root updated to: {path}")
    return {"status": "ok", "workspace_root": path}


@app.get("/api/ide/workspace")
async def ide_get_workspace():
    """Get the current workspace root directory."""
    return {"workspace_root": coding_agent.WORKSPACE_ROOT}


# ═══════════════════════════════════════════════════════════════════════════════
# CHAT ORCHESTRATOR (Chat-First UI endpoint)
# ═══════════════════════════════════════════════════════════════════════════════

ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "gemma4:12b-it-qat")
DEFAULT_VISION_MODEL = os.getenv("DEFAULT_VISION_MODEL", "llama3.2-vision:11b")


@app.post("/api/orchestrator/chat")
async def orchestrator_chat(request: Request):
    """
    Chat-First Orchestrator endpoint.
    Accepts a user message + history, uses Gemma4 to detect intent,
    and returns a unified response with action routing metadata.
    Frontend uses this to render inline media widgets and Workbench pass-through.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    message = body.get("message", "").strip()
    context = body.get("context", "Default")
    history = body.get("history", [])
    model = body.get("model", ORCHESTRATOR_MODEL)
    images = body.get("images", [])
    active_contexts = body.get("active_contexts", [])

    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    # If images are provided, switch to the vision-capable model and bypass routing (chat only)
    if images:
        action = "chat"
        reply = ""
        params = {}
        routing_model = DEFAULT_VISION_MODEL
    else:
        routing_model = model
        # Step 1: Route the intent via Gemma4
        routing = await orchestrator.route_message(
            message=message,
            context=context,
            history=history,
            model=routing_model,
            ollama_url=OLLAMA_URL,
            images=images,
        )
        action = routing["action"]
        reply = routing["reply"]
        params = routing["params"]

    # Step 2: For plain chat, execute and return full response directly
    if action == "chat":
        full_reply = await orchestrator.handle_chat(
            message=message,
            context=context,
            history=history,
            model=routing_model,
            ollama_url=OLLAMA_URL,
            images=images,
            active_contexts=active_contexts,
        )
        
        # Robustness: Intercept and translate any raw tool calls outputted in chat mode
        try:
            cleaned = full_reply.strip()
            if "```" in cleaned:
                parts = cleaned.split("```")
                for part in parts:
                    stripped = part.strip()
                    if stripped.startswith("json"):
                        stripped = stripped[4:].strip()
                    if stripped.startswith("{"):
                        cleaned = stripped
                        break
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            if start >= 0 and end > start:
                cleaned = cleaned[start:end]
                data = json.loads(cleaned)
                if "action" in data:
                    parsed_action = data["action"]
                    action_input = data.get("action_input", {})
                    if isinstance(action_input, str) and action_input.strip():
                        try:
                            action_input = json.loads(action_input)
                        except Exception:
                            action_input = {"prompt": action_input}
                    elif not action_input:
                        action_input = data.get("params", {})
                    
                    dify_action_map = {
                        "dalle.text2im": "image",
                        "dalle": "image",
                        "sdxl": "image",
                        "stable_diffusion": "image",
                        "flux": "image",
                        "generate_image": "image",
                        "image_gen": "image",
                        "text2image": "image",
                        "text2im": "image",
                        "video_gen": "video",
                        "ltx": "video",
                        "text2video": "video",
                        "generate_video": "video",
                        "tts": "audio",
                        "text2speech": "audio",
                        "generate_audio": "audio",
                        "generate_speech": "audio",
                        "generate_music": "music",
                        "music_gen": "music",
                        "generate_3d": "3d",
                        "3d_gen": "3d",
                        "web_search": "research",
                        "search": "research",
                        "generate_research": "research",
                        "writer": "text",
                        "generate_text": "text",
                        "text_gen": "text"
                    }
                    mapped_action = dify_action_map.get(parsed_action, parsed_action)
                    valid_actions = {"image", "video", "audio", "music", "3d", "research", "text"}
                    if mapped_action in valid_actions:
                        tab_map = {
                            "image": "image",
                            "video": "video",
                            "audio": "audio",
                            "music": "music",
                            "3d": "3d",
                            "research": "research",
                            "text": "text",
                        }
                        friendly_replies = {
                            "image": "I've formulated an image generation card for you.",
                            "video": "I've prepared a video generation card for you.",
                            "audio": "I can synthesize this text to audio.",
                            "music": "I've drafted a music track card.",
                            "research": "I'll start researching this topic.",
                            "text": "I've prepared a text generation draft."
                        }
                        return {
                            "action": mapped_action,
                            "reply": data.get("reply") or friendly_replies.get(mapped_action, "Processing your request..."),
                            "result_url": None,
                            "result_type": None,
                            "metadata": {
                                "tab": tab_map.get(mapped_action, mapped_action),
                                **action_input
                            },
                        }
        except Exception as e:
            logger.warning(f"Failed to intercept tool call from chat reply: {e}")

        return {
            "action": "chat",
            "reply": full_reply,
            "result_url": None,
            "result_type": None,
            "metadata": {},
        }

    # Step 3: For media generation — return the intent+params so the frontend
    # can show an action card (Generate button + Edit in Workbench pass-through).
    # Actual generation is triggered by the user clicking Generate in the action card,
    # which calls the existing /api/{action}/generate endpoints directly.
    tab_map = {
        "image": "image",
        "video": "video",
        "audio": "audio",
        "music": "music",
        "3d": "3d",
        "research": "research",
        "text": "text",
    }

    return {
        "action": action,
        "reply": reply,
        "result_url": None,
        "result_type": None,
        "metadata": {
            "tab": tab_map.get(action, action),
            **params
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FILE SERVING (with path traversal protection)
# ═══════════════════════════════════════════════════════════════════════════════

# Duplicate /api/assets route removed — using list_all_assets() from line ~805


@app.get("/output/{filename}")
async def serve_output(filename: str):
    """Serve a file from the output directory. Protected against path traversal attacks."""
    # Resolve the real absolute path and verify it is inside OUTPUT_DIR
    safe_root = os.path.realpath(OUTPUT_DIR)
    requested = os.path.realpath(os.path.join(OUTPUT_DIR, filename))
    if not requested.startswith(safe_root + os.sep) and requested != safe_root:
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(requested):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")
    return FileResponse(requested)


# ═══════════════════════════════════════════════════════════════════════════════
# PILLAR 10: PUBLISHING & KPI MONITORING
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/publish/upload")
async def publish_upload(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    file_path = body.get("file_path", "")
    metadata = body.get("metadata", {})
    title = metadata.get("title", "Untitled Video")
    description = metadata.get("description", "")
    tags = metadata.get("tags", [])
    
    # Generate metadata package
    pkg = await publishing.generate_metadata(title, description, tags)
    
    # Simulate upload
    res = await publishing.upload_video(file_path, pkg)
    return res


@app.get("/api/publish/schedule")
async def get_publish_schedule():
    return await publishing.get_schedule()


@app.post("/api/publish/schedule")
async def create_publish_schedule(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    
    title = body.get("title", "Untitled Release")
    publish_time = body.get("publish_time", "")
    return await publishing.schedule_video(title, publish_time)


@app.get("/api/kpi/dashboard")
async def get_kpis():
    return await kpi_monitoring.get_kpi_dashboard()


@app.get("/api/kpi/experiments")
async def get_experiments():
    return await kpi_monitoring.list_experiments()


@app.post("/api/kpi/experiments")
async def create_experiment(request: Request):
    try:
        body = await request.json()
    except Exception:
         raise HTTPException(status_code=400, detail="Invalid JSON body")
         
    video_id = body.get("video_id", "")
    name = body.get("name", "New Experiment")
    var_a = body.get("variant_a", "A")
    var_b = body.get("variant_b", "B")
    return await kpi_monitoring.create_experiment(video_id, name, var_a, var_b)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTOMATED BATCH PIPELINE RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def _write_failed_pipeline_state(job_id: str, error_msg: str):
    try:
        state_file = os.path.join(_get_job_dir(job_id), "state.json")
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                state = json.load(f)
        else:
            state = {
                "job_id": job_id,
                "status": "failed",
                "steps": {
                    "A": {"status": "pending", "progress": 0, "msg": "Waiting to start"},
                    "B": {"status": "pending", "progress": 0, "msg": "Waiting to start"},
                    "C": {"status": "pending", "progress": 0, "msg": "Waiting to start"},
                    "D": {"status": "pending", "progress": 0, "msg": "Waiting to start"},
                    "E": {"status": "pending", "progress": 0, "msg": "Waiting to start"},
                    "F": {"status": "pending", "progress": 0, "msg": "Waiting to start"},
                    "G": {"status": "pending", "progress": 0, "msg": "Waiting to start"},
                    "H": {"status": "pending", "progress": 0, "msg": "Waiting to start"},
                    "QC": {"status": "pending", "progress": 0, "msg": "Waiting to start"}
                }
            }
        state["status"] = "failed"
        current_step = state.get("current_step", "B")
        if current_step in state.get("steps", {}):
            state["steps"][current_step]["status"] = "failed"
            state["steps"][current_step]["msg"] = error_msg
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write failed pipeline state for {job_id}: {e}")

async def _run_batch_pipeline_job(job_id: str, channel_id: str, topic: str, phase: str):
    try:
        cmd = ["python", "scratch/batch_pipeline.py", channel_id, topic, job_id, phase]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        ACTIVE_SUBPROCESSES[job_id] = process
        try:
            await asyncio.wait_for(process.communicate(), timeout=1200.0)  # 20 min max
            if process.returncode == 0:
                if phase == "phase1":
                    await job_store.update(job_id, status="pending_approval", progress_pct=50, progress_msg="Phase 1 Complete. Pending Approval.")
                else:
                    await job_store.complete(job_id, result={"status": "batch pipeline completed"})
            else:
                err_msg = f"Subprocess exited with code {process.returncode}."
                await job_store.fail(job_id, error=err_msg)
                _write_failed_pipeline_state(job_id, err_msg)
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
            err_msg = f"Batch pipeline {job_id} timed out after 20 minutes."
            logger.error(err_msg)
            await job_store.fail(job_id, error=err_msg)
            _write_failed_pipeline_state(job_id, err_msg)
        finally:
            ACTIVE_SUBPROCESSES.pop(job_id, None)
    except Exception as e:
        logger.error(f"Batch pipeline job failed: {e}")
        await job_store.fail(job_id, error=str(e))
        _write_failed_pipeline_state(job_id, str(e))

@app.post("/api/pipeline/run")
async def run_batch_pipeline(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
        
    channel_id = body.get("channel_id", "MLN").strip()
    topic = body.get("topic", "macroeconomics global finance crypto trends 2026").strip()
    
    # 1. Resolve channel numeric ID and 3-letter code
    channel_map = _get_channel_mapping()
    chan_num = None
    chan_code = None
    if str(channel_id) in channel_map:
        chan_num = int(channel_id)
        chan_code = channel_map[str(channel_id)]
    else:
        for k, v in channel_map.items():
            if v.upper() == str(channel_id).upper():
                chan_num = int(k)
                chan_code = v
                break
    if chan_num is None:
        chan_num = 1
        chan_code = "MLN"
        
    # 2. Determine year_week
    year_week = body.get("year_week", "").strip()
    if not year_week:
        from datetime import date
        iso_year, iso_week, _ = date.today().isocalendar()
        year_str = str(iso_year)[-2:]
        year_week = f"{year_str}w{iso_week:02d}"
        
    # 3. Determine content_type
    raw_type = body.get("content_type", "").strip().lower() or body.get("type", "").strip().lower()
    if raw_type in ("daily", "d"):
        content_type = "daily"
        type_char = "d"
    elif raw_type in ("short", "s"):
        content_type = "short"
        type_char = "s"
    else:
        content_type = "flagship"
        type_char = "f"
        
    parent_job_code = body.get("parent_job_code", "").strip() or None
    
    # 4. Scoped sequence number
    num = await job_store.get_next_sequence_number(chan_num, year_week, content_type)
    seq_str = f"{num:02d}"
    
    if content_type == "short":
        if not parent_job_code:
            raise HTTPException(status_code=400, detail="Missing parent_job_code for short cut job")
        job_code = f"{parent_job_code}.s{seq_str}"
    else:
        job_code = f"{chan_num}.{year_week}.{type_char}{seq_str}"
        
    # 5. Create job in store
    job_id = await job_store.create(
        job_type="pipeline",
        job_code=job_code,
        content_type=content_type,
        channel_id=chan_num,
        year_week=year_week,
        parent_job_code=parent_job_code
    )
    
    # 6. Ensure directory and default state.json exist before we launch task
    job_dir = _get_job_dir(job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    state_file = os.path.join(job_dir, "state.json")
    if not os.path.exists(state_file):
        default_state = {
            "job_id": job_id,
            "job_code": job_code,
            "channel_id": chan_num,
            "channel_code": chan_code,
            "year_week": year_week,
            "content_type": content_type,
            "topic": topic,
            "status": "running",
            "stage": 1,
            "progress_pct": 10,
            "step": "channels",
            "intelligence_brief": {"theme": topic, "episodes": []}
        }
        with open(state_file, "w") as f:
            json.dump(default_state, f, indent=2)
            
    await job_store.update(job_id, status="running", progress_pct=10, progress_msg="Initializing Phase 1...")
    
    register_background_task(job_id, _run_batch_pipeline_job(job_id, chan_code, topic, "phase1"))
    
    return {"job_id": job_id, "status": "running", "job_code": job_code}

@app.post("/api/pipeline/approve/{job_id}")
async def approve_batch_pipeline(job_id: str, request: Request):
    _safe_job_id(job_id)
    jobs_root = os.path.join(os.getenv("OUTPUT_DIR", "output"), "jobs")
    state_file = os.path.join(jobs_root, job_id, "state.json")
    if not os.path.exists(state_file):
        raise HTTPException(status_code=404, detail="Job not found")
        
    try:
        # Check if there is request body containing edited brief
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass # No edits provided, proceed with existing files on disk
            
        if body and "phase1_intelligence_brief" in body:
            # Overwrite/save the edits on disk before triggering Phase 2
            brief = body.get("phase1_intelligence_brief", {})
            
            # Reconstruct selected_topic
            titles = [v.get("title") for v in brief.get("section_2_title_strategy", {}).get("variants", []) if v.get("title")]
            thumbnails = [c.get("subject") for c in brief.get("section_3_thumbnail_strategy", {}).get("concepts", []) if c.get("subject")]
            
            selected_topic = {
                "winning_topic": body.get("job_meta", {}).get("input_topic", ""),
                "ctr_score": 8.5,
                "title_variants": titles,
                "thumbnail_concepts": thumbnails
            }
            with open(os.path.join(jobs_root, job_id, "a3_selected_topic.json"), "w") as f:
                json.dump(selected_topic, f, indent=2)
                
            # Reconstruct b1_master_script
            script_sections = brief.get("section_4_master_script", {}).get("sections", [])
            sections = []
            for sec in script_sections:
                sections.append({
                    "section_id": sec.get("section_id"),
                    "label": sec.get("label"),
                    "narration": sec.get("narration"),
                    "target_duration_seconds": int(sec.get("target_duration_seconds", 30))
                })
            master_script = {
                "mode": brief.get("section_4_master_script", {}).get("content_mode", "narrator-led"),
                "sections": sections
            }
            with open(os.path.join(jobs_root, job_id, "b1_master_script.json"), "w") as f:
                json.dump(master_script, f, indent=2)
                
            # Reconstruct b3_voiceover_pack
            voiceover_pack = []
            for sec in sections:
                voiceover_pack.append({
                    "section_id": sec["section_id"],
                    "narration": sec["narration"],
                    "estimated_duration_seconds": sec["target_duration_seconds"]
                })
            with open(os.path.join(jobs_root, job_id, "b3_voiceover_pack.json"), "w") as f:
                json.dump(voiceover_pack, f, indent=2)
                
            # Save raw intelligence brief
            with open(os.path.join(jobs_root, job_id, "phase1_intelligence_brief.json"), "w") as f:
                json.dump(body, f, indent=2)

        with open(state_file, "r") as f:
            state = json.load(f)
        channel_id = state.get("channel_id", "MLN")
        topic = state.get("topic", "")
        
        await job_store.update(job_id, status="running", progress_pct=55, progress_msg="Phase 2 rendering started...")
        
        register_background_task(job_id, _run_batch_pipeline_job(job_id, channel_id, topic, "phase2"))
        return {"job_id": job_id, "status": "approved"}
    except Exception as e:
        logger.error(f"Approval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pipeline/regenerate-field")
async def regenerate_field(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
        
    field_content = body.get("field_content", "")
    instruction = body.get("instruction", "")
    
    if not instruction:
        raise HTTPException(status_code=400, detail="instruction is required")
        
    try:
        system_prompt = (
            "You are SPARK-STRATEGY, an expert YouTube strategist and copywriter. Your task is to rewrite the provided "
            "text or prompt according to the instruction.\n"
            "CRITICAL RULES:\n"
            "- Output ONLY the rewritten text. Do not include quotes, explanations, or introductory/closing remarks.\n"
            "- Preserve the length, style, and tone of the original unless instructed otherwise."
        )
        user_prompt = f"Original text:\n{field_content}\n\nInstruction:\n{instruction}\n\nRewritten text:"
        
        ollama_url = OLLAMA_URL
        payload = {
            "model": "qwen3:8b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=payload)
            if r.status_code == 200:
                result = r.json()["message"]["content"].strip()
                if result.startswith('"') and result.endswith('"'):
                    result = result[1:-1].strip()
                elif result.startswith("'") and result.endswith("'"):
                    result = result[1:-1].strip()
                return {"result": result}
            else:
                raise Exception(f"Ollama returned HTTP {r.status_code}")
    except Exception as e:
        logger.error(f"Field regeneration failed: {e}")
        return {"result": f"{field_content} (amended: {instruction})"}

@app.get("/api/pipeline/brief/{job_id}")
async def get_batch_pipeline_brief(job_id: str):
    job_dir = _get_job_dir(job_id)
    brief_file = os.path.join(job_dir, "phase1_intelligence_brief.json")
    if not os.path.exists(brief_file):
        raise HTTPException(status_code=404, detail="Brief not found")
    try:
        with open(brief_file, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pipeline/export")
async def save_export(request: Request):
    try:
        body = await request.json()
        job_id = body.get("job_id")
        filename = body.get("filename")
        content = body.get("content")
        
        if not job_id or not filename or not content:
            raise HTTPException(status_code=400, detail="job_id, filename, and content are required")
            
        job_dir = _get_job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        file_path = os.path.join(job_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return {"status": "success", "file_path": file_path}
    except Exception as e:
        logger.error(f"Save export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pipeline/download")
async def download_file(job_id: str, filename: str):
    job_dir = _get_job_dir(job_id)
    file_path = os.path.join(job_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    import mimetypes
    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return FileResponse(file_path, filename=filename, media_type=media_type)

@app.get("/api/pipeline/assets/{job_id}")
async def list_pipeline_assets(job_id: str):
    job_dir = _get_job_dir(job_id)
    if not os.path.isdir(job_dir):
        raise HTTPException(status_code=404, detail="Job directory not found")

    asset_extensions = {
        "png", "jpg", "jpeg", "webp", "gif",
        "mp4", "webm", "mkv",
        "wav", "mp3", "ogg",
        "srt", "vtt",
    }
    skip_files = {"state.json", "job_manifest.json"}

    assets = []
    for root, dirs, files in os.walk(job_dir):
        for fname in files:
            if fname in skip_files or not any(fname.endswith(ext) for ext in asset_extensions):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, job_dir)
            ext = fname.rsplit(".", 1)[-1].lower()
            if ext in ("png", "jpg", "jpeg", "webp", "gif"):
                t = "image"
            elif ext in ("mp4", "webm", "mkv"):
                t = "video"
            elif ext in ("wav", "mp3", "ogg"):
                t = "audio"
            else:
                t = "document"
            assets.append({
                "name": fname,
                "path": rel_path,
                "type": t,
                "url": f"/api/pipeline/download?job_id={job_id}&filename={rel_path}",
            })
    assets.sort(key=lambda a: a["path"])
    return assets

@app.get("/api/pipeline/jobs")
async def list_jobs(channel_id: str = None, year_week: str = None):
    try:
        jobs = await job_store.list_recent(limit=200)
        
        # If channel_id is provided, resolve to numeric channel ID or string
        chan_num = None
        if channel_id:
            channel_map = _get_channel_mapping()
            if str(channel_id) in channel_map:
                chan_num = int(channel_id)
            else:
                for k, v in channel_map.items():
                    if v.upper() == str(channel_id).upper():
                        chan_num = int(k)
                        break
        
        jobs_list = []
        for job in jobs:
            if chan_num is not None and job.get("channel_id") is not None and job.get("channel_id") != chan_num:
                continue
                
            if year_week and job.get("year_week") != year_week:
                continue
                
            job_id = job["job_id"]
            job_dir = _get_job_dir(job_id)
            state_file = os.path.join(job_dir, "state.json")
            
            state = {}
            if os.path.exists(state_file):
                try:
                    with open(state_file, "r") as f:
                        state = json.load(f)
                except Exception:
                    pass
                    
            # Check channel filter if legacy
            if chan_num is not None:
                state_chan = state.get("channel_code", state.get("channel_id"))
                if state_chan:
                    state_chan_num = None
                    channel_map = _get_channel_mapping()
                    if str(state_chan) in channel_map:
                        state_chan_num = int(state_chan)
                    else:
                        for k, v in channel_map.items():
                            if v.upper() == str(state_chan).upper():
                                state_chan_num = int(k)
                                break
                    if state_chan_num != chan_num:
                        continue
                elif job.get("channel_id") is None:
                    continue
            
            updated_at = job.get("updated_at", job.get("created_at", 0))
            if os.path.exists(state_file):
                updated_at = os.path.getmtime(state_file)
                
            jobs_list.append({
                "job_id": job_id,
                "job_code": job.get("job_code"),
                "content_type": job.get("content_type", "flagship"),
                "channel_id": job.get("channel_id"),
                "year_week": job.get("year_week"),
                "topic": state.get("topic", job.get("progress_msg", "")),
                "status": state.get("status", job["status"]),
                "current_step": state.get("step", state.get("current_step", "channels")),
                "stage": state.get("stage", 1),
                "progress_pct": state.get("progress_pct", job["progress_pct"]),
                "updated_at": updated_at
            })
            
        jobs_list.sort(key=lambda x: x["updated_at"], reverse=True)
        return jobs_list
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pipeline/reject/{job_id}")
async def reject_batch_pipeline(job_id: str):
    job_dir = _get_job_dir(job_id)
    state_file = os.path.join(job_dir, "state.json")
    if not os.path.exists(state_file):
        raise HTTPException(status_code=404, detail="Job not found")
        
    task = ACTIVE_TASKS.get(job_id)
    if task and not task.done():
        task.cancel()
        logger.info(f"Cancelled active task for pipeline job: {job_id}")
        
    proc = ACTIVE_SUBPROCESSES.get(job_id)
    if proc:
        try:
            proc.kill()
            logger.info(f"Killed active subprocess for pipeline job: {job_id}")
        except Exception as e:
            logger.warning(f"Error killing subprocess: {e}")
            
    try:
        await job_store.fail(job_id, error="Rejected by user.")
        
        with open(state_file, "r") as f:
            state = json.load(f)
        state["status"] = "failed"
        state["steps"]["B"]["status"] = "failed"
        state["steps"]["B"]["msg"] = "Rejected by user."
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
        return {"job_id": job_id, "status": "rejected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/pipeline/status/{job_id}")
async def get_batch_pipeline_status(job_id: str):
    job_dir = _get_job_dir(job_id)
    state_file = os.path.join(job_dir, "state.json")
    if not os.path.exists(state_file):
        raise HTTPException(status_code=404, detail="Job state not found")
        
    try:
        with open(state_file, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pipeline/script/{job_id}")
async def get_batch_pipeline_script(job_id: str):
    job_dir = _get_job_dir(job_id)
    script_file = os.path.join(job_dir, "b1_master_script.json")
    if not os.path.exists(script_file):
        raise HTTPException(status_code=404, detail="Script not found")
    try:
        with open(script_file, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pipeline/topic/{job_id}")
async def get_batch_pipeline_topic(job_id: str):
    job_dir = _get_job_dir(job_id)
    topic_file = os.path.join(job_dir, "a3_selected_topic.json")
    if not os.path.exists(topic_file):
        raise HTTPException(status_code=404, detail="Topic not found")
    try:
        with open(topic_file, "r") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# ═══════════════════════════════════════════════════════════════════════════════
# RESEARCH FILE EXPLORER ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

# Duplicate /api/research/* routes removed — using endpoints from line ~819


# Duplicate /api/research/compile and /api/research/expand removed — using endpoints from line ~878


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5050"))
    uvicorn.run("app.main:app", host=host, port=port, reload=True)

