---
chapter_id: X04
title: "Local Platform Layer"
layer: "Foundation"
status: "implemented"
purpose: "Make every service discoverable and callable by the FastAPI gateway"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - ".env file"
  - "docker-compose.yml"
  - "Dockerfile"
outputs:
  - "Running containers (4)"
  - "Health check response"
  - "GPU status"
qc_gates:
  - "GET /health returns all services online"
  - "All Docker containers running"
  - "GPU accessible via nvidia-smi"
default_tools:
  primary: "FastAPI + Docker Compose"
  fallback: "Manual service startup"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X04"
  run: "run_X04"
  score: "score_X04"
  retry: "retry_X04"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X04 — Local Platform Layer

## Chapter Card
**Chapter:** `X04 — Local Platform Layer`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Make every service discoverable and callable by the FastAPI gateway without guessing ports, URLs, or auth.  
**Last Verified:** 2026-06-15

**Actual Implementation:**
- **FastAPI Gateway:** `app/main.py` (v1.2.0) — port `5050`
- **Config:** Environment variables via `.env` file, loaded at startup
- **Health Check:** `GET /health` — pings all services in parallel

**Actual Services & Ports:**
| Service | Internal URL | Host Port | Docker Container | Status |
|---------|-------------|-----------|------------------|--------|
| FastAPI Gateway | `http://localhost:5050` | 5050 | `spark-gateway` | ✅ |
| Ollama LLM | `http://host.docker.internal:11434` | 11434 | Host process | ✅ |
| ComfyUI | `http://host.docker.internal:8188` | 8188 | Host process | ✅ |
| Whisper STT | `http://whisper-stt:9000` | 8010 (mapped) | `spark-whisper` | ✅ |
| F5-TTS | `http://f5-tts:8000` | 8020 (mapped) | `spark-f5tts` | ✅ |
| Qdrant | `http://qdrant:6333` | 6333 | `spark-qdrant` | ✅ |

**Environment Variables (from `main.py:38-44`):**
```bash
OLLAMA_URL=http://host.docker.internal:11434
COMFYUI_URL=http://host.docker.internal:8188
WHISPER_URL=http://whisper-stt:9000
F5_TTS_URL=http://f5-tts:8000
QDRANT_URL=http://qdrant:6333
OUTPUT_DIR=/app/output
COMFYUI_OUTPUT_DIR=/comfyui-output
```

**Quality Gates:**
- Gate 1: `GET /health` returns `{"status": "online", "services": {...}}`
- Gate 2: All service containers running (`docker compose ps`)
- Gate 3: GPU accessible (`GET /api/gpu/status` returns nvidia-smi data)

---

## 1) Quickstart (Golden Path)

### Goal
Start the Spark Media Factory and verify all services are healthy.

### When to run
- First-time setup
- After system restart
- After Docker image updates

### Golden Path Steps
1) **Start Node 2 services** (Ollama + ComfyUI on host):
   ```bash
   # Start Ollama
   ollama serve
   
   # Verify models loaded
   ollama list
   ```
   Expected: Ollama running on port 11434, models visible

2) **Start Node 1 stack** (Docker Compose):
   ```bash
   # From project root
   chmod +x start.sh
   ./start.sh
   ```
   OR manually:
   ```bash
   docker compose up --build -d
   ```
   Expected: 4 containers running (spark-gateway, spark-qdrant, spark-whisper, spark-f5tts)

3) **Verify all services**:
   ```bash
   docker compose ps
   curl http://localhost:5050/health
   ```
   Expected: All containers "Up", health endpoint returns online status

4) **Check GPU status**:
   ```bash
   curl http://localhost:5050/api/gpu/status
   ```
   Expected: GPU info with VRAM usage, temperature, utilization

5) **Access Web UI**:
   Open browser to `http://localhost:5050`
   Expected: Glassmorphic UI loads with service status indicators

### Done looks like
- [ ] All 4 Docker containers running
- [ ] `GET /health` returns all services online
- [ ] `GET /api/gpu/status` shows GPU info
- [ ] Web UI accessible at `http://localhost:5050`
- [ ] Smoke tests pass: `python run_smoke_tests.py`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| `.env` file | Project root | Environment variables for service URLs |
| `docker-compose.yml` | Project root | Service definitions and port mappings |
| `Dockerfile` | Project root | Gateway container build instructions |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Running containers | `docker compose ps` | 4 containers: gateway, qdrant, whisper, f5tts |
| Health check response | `GET /health` | JSON with service status |
| GPU status | `GET /api/gpu/status` | nvidia-smi data |

### Definition of Done (DoD)
All services responding to health checks + GPU accessible + Web UI loadable.

---

## 3) Port Registry (Actual Implementation)

**Source of truth:** `docker-compose.yml` + `app/main.py:38-44`

| Service | Internal URL | Host Port | Protocol | Notes |
|---------|-------------|-----------|----------|-------|
| FastAPI Gateway | `http://localhost:5050` | 5050 | HTTP | Main entry point |
| Ollama LLM | `http://host.docker.internal:11434` | 11434 | HTTP | Host process, not containerized |
| ComfyUI | `http://host.docker.internal:8188` | 8188 | HTTP | Host process, not containerized |
| Whisper STT | `http://whisper-stt:9000` | 8010 | HTTP | Mapped from container port 9000 |
| F5-TTS | `http://f5-tts:8000` | 8020 | HTTP | Mapped from container port 8000 |
| Qdrant | `http://qdrant:6333` | 6333 | HTTP | Vector database |
| Qdrant gRPC | `http://qdrant:6334` | 6334 | gRPC | Optional gRPC interface |

**Config keys (from `main.py:38-44`):**
```bash
OLLAMA_URL=http://host.docker.internal:11434
COMFYUI_URL=http://host.docker.internal:8188
WHISPER_URL=http://whisper-stt:9000
F5_TTS_URL=http://f5-tts:8000
QDRANT_URL=http://qdrant:6333
OUTPUT_DIR=/app/output
COMFYUI_OUTPUT_DIR=/comfyui-output
```

---

## 4) Service Registry (Actual Implementation)

**Source of truth:** `docker-compose.yml` + `app/main.py:50-69`

| Service ID | Display Name | Base URL | Health Check | Start Method | Notes |
|------------|--------------|----------|--------------|--------------|-------|
| `gateway` | Spark Gateway | `http://localhost:5050` | `GET /health` | Docker Compose | FastAPI app |
| `ollama` | Ollama LLM | `http://host.docker.internal:11434` | `GET /api/tags` | Host process | Models: gemma4, qwen3 |
| `comfyui` | ComfyUI | `http://host.docker.internal:8188` | `GET /system_stats` | Host process | Image/video/music gen |
| `whisper` | Whisper STT | `http://whisper-stt:9000` | `GET /docs` | Docker Container | faster-whisper v1.6.0 |
| `f5tts` | F5-TTS | `http://f5-tts:8000` | `GET /` | Docker Container | Speech synthesis |
| `qdrant` | Qdrant | `http://qdrant:6333` | `GET /healthz` | Docker Container | Vector database |

**Health Check Implementation (from `main.py:155-173`):**
```python
@app.get("/health")
async def health_check():
    async def _check(name: str, url: str) -> tuple[str, str]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(url)
                return name, "online" if r.status_code == 200 else "error"
        except Exception:
            return name, "offline"
    
    results = await asyncio.gather(
        _check("ollama",  f"{OLLAMA_URL}/api/tags"),
        _check("comfyui", f"{COMFYUI_URL}/system_stats"),
        _check("whisper", f"{WHISPER_URL}/docs"),
        _check("f5tts",   f"{F5_TTS_URL}/"),
    )
    services = {"gateway": "online"} | dict(results)
    return {"status": "online", "services": services}
```

---

## 5) Tooling (Approved Stack)

### Primary (default)
- **Gateway Framework:** FastAPI (Python 3.10+)
  - **Version:** 0.115.0 (pinned in `requirements.txt`)
  - **Compute notes:** Lightweight, async-native
  - **Strengths:** Fast development, automatic OpenAPI docs, SSE support
  - **Weaknesses:** No built-in auth (added via middleware)

### LLM Inference
- **Ollama** (primary)
  - **Models:** gemma4:12b-it-qat (orchestrator), qwen3:8b/14b (coding)
  - **Endpoint:** `http://host.docker.internal:11434`
  - **Strengths:** Local, private, fast inference
  - **Weaknesses:** Requires GPU VRAM

- **vLLM** (alternative, for coding agent)
  - **Models:** Any vLLM-compatible model
  - **Endpoint:** `http://host.docker.internal:8000`
  - **When to use:** When Ollama is overloaded or for specific model requirements

### Media Generation
- **ComfyUI** (image/video/music/3D)
  - **Models:** FLUX, LTX-Video, ACE-Step, Hunyuan3D
  - **Endpoint:** `http://host.docker.internal:8188`
  - **Strengths:** Flexible workflow engine, GPU-accelerated
  - **Weaknesses:** Complex setup, VRAM-intensive

### Audio
- **Whisper STT** (speech-to-text)
  - **Model:** faster-whisper large-v3 (float16)
  - **Endpoint:** `http://whisper-stt:9000`
  - **Strengths:** High accuracy, VAD support
  - **Weaknesses:** Requires GPU for real-time

- **F5-TTS** (text-to-speech)
  - **Languages:** en, es, pt, de
  - **Endpoint:** `http://f5-tts:8000`
  - **Strengths:** Natural voice quality
  - **Weaknesses:** Limited language support

### Storage
- **Qdrant** (vector database)
  - **Purpose:** RAG document storage and retrieval
  - **Endpoint:** `http://qdrant:6333`
  - **Strengths:** Fast similarity search, easy setup
  - **Weaknesses:** Single-node only in this setup

---

## 6) Procedure (Operator Steps)

### Step 1 — Start Ollama (Host)
- **Inputs:** None
- **Action:** Run `ollama serve` on host machine
- **Expected output:** Ollama listening on port 11434
- **Common failures:** Port already in use, model not found
- **Fix:** Kill existing process, run `ollama pull <model>`

### Step 2 — Start Docker Stack
- **Inputs:** `.env` file, `docker-compose.yml`
- **Action:** Run `docker compose up --build -d`
- **Expected output:** 4 containers running
- **Common failures:** GPU not available, port conflicts
- **Fix:** Check `nvidia-smi`, verify ports not in use

### Step 3 — Verify Health
- **Inputs:** None
- **Action:** `curl http://localhost:5050/health`
- **Expected output:** `{"status": "online", "services": {...}}`
- **Common failures:** Service offline, timeout
- **Fix:** Check container logs with `docker logs <container>`

### Step 4 — Test Endpoints
- **Inputs:** None
- **Action:** Test key endpoints
- **Expected output:** Successful responses
- **Common failures:** 422 Validation Error, 500 Internal Error
- **Fix:** Check request body format, review server logs

---

## 7) Troubleshooting (Top Issues)

### Issue 1 — "Cannot connect to Ollama"
- **Cause:** Ollama not running on host
- **Fix:** Run `ollama serve` in separate terminal
- **Prevention:** Add to startup script

### Issue 2 — "GPU not available" in Docker
- **Cause:** NVIDIA Container Toolkit not installed
- **Fix:** Install nvidia-docker2, restart Docker
- **Prevention:** Run `nvidia-smi` before starting stack

### Issue 3 — "Port 5050 already in use"
- **Cause:** Another process using port
- **Fix:** `lsof -i :5050` then kill process, or change port in `.env`
- **Prevention:** Use consistent port allocation

### Issue 4 — "Whisper STT timeout"
- **Cause:** Large audio file, slow GPU
- **Fix:** Use smaller audio, increase timeout
- **Prevention:** Monitor GPU usage with `/api/gpu/status`

### Issue 5 — "Qdrant connection refused"
- **Cause:** Qdrant container not started
- **Fix:** `docker compose restart qdrant`
- **Prevention:** Check `docker compose ps` after startup

---

## 8) Metrics to Record

- `runtime_seconds` — Startup time
- `gpu_vram_peak` — Maximum VRAM usage
- `services_online` — Count of healthy services
- `health_check_latency` — Response time for `/health`
- `failure_reason` — Error message if startup fails

---

## 9) Change Log

- 2026-06-15 — Initial implementation with actual codebase content
- 2025-12-24 — Original template created