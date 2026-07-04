# Spark Test Tool — Sonet Code Review Notes
**Reviewed:** June 2026  
**Reviewer:** Claude Sonnet (Antigravity)  
**Scope:** Full codebase review — security, modernisation, improvements  

---

## 🔴 CRITICAL SECURITY ISSUES (Fix First)

### SEC-01 — CREDENTIALS COMMITTED IN `.env` (CRITICAL)
**File:** `.env` lines 26-27  
**Problem:** Real Yahoo email address and App Password are hardcoded in `.env` and this file is **COPY'd into the Docker image** in `Dockerfile` line 13 (`COPY .env .`). This means anyone with access to the Docker image has your email credentials in plaintext.  

```
YAHOO_EMAIL=prdp1200@yahoo.com
YAHOO_APP_PASSWORD=izbmlupxfjpzdpln   ← LIVE APP PASSWORD IN PLAIN TEXT
```

**Fix:**
1. Immediately revoke the Yahoo App Password at https://login.yahoo.com/account/security
2. Remove the `.env` file from the Docker image — delete line `COPY .env .` from `Dockerfile`
3. Add `.env` to `.gitignore` (create `.gitignore` if it doesn't exist)
4. Pass secrets via `docker-compose.yml` `environment:` section or Docker Secrets, **not** via a copied `.env` file
5. Use a `.env.example` file with placeholder values for documentation purposes

**Dockerfile fix (remove line 13):**
```dockerfile
# REMOVE THIS LINE:
# COPY .env .
```

**docker-compose.yml fix — inject secrets as env vars directly:**
```yaml
environment:
  - YAHOO_EMAIL=${YAHOO_EMAIL}
  - YAHOO_APP_PASSWORD=${YAHOO_APP_PASSWORD}
```
Then use a `.env` that is never copied into the image (Docker Compose reads it from the host automatically).

---

### SEC-02 — WILDCARD CORS ALLOWS ALL ORIGINS (HIGH)
**File:** `app/main.py` lines 53-59  
**Problem:** `allow_origins=["*"]` combined with `allow_credentials=True` is a CORS misconfiguration. Browsers block this combination due to the CORS spec, but it also means any domain can make cross-origin requests to this API.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # ← Too broad
    allow_credentials=True,   # ← Cannot be combined with wildcard
    ...
)
```

**Fix:** Either restrict to specific trusted origins, or remove `allow_credentials=True` if credentials are not needed. Prefer a configurable allow-list:

```python
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5050").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

### SEC-03 — PATH TRAVERSAL IN FILE SERVE ENDPOINT (HIGH)
**File:** `app/main.py` lines 473-478  
**Problem:** The `/output/{filename}` endpoint does not validate that the filename is safe. A crafted request like `/output/../app/main.py` could leak internal source files.

```python
@app.get("/output/{filename}")
async def serve_output(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)  # ← No path traversal check
    if os.path.exists(file_path):
        return FileResponse(file_path)
```

**Fix:** Resolve the absolute path and verify it is within `OUTPUT_DIR`:

```python
@app.get("/output/{filename}")
async def serve_output(filename: str):
    # Prevent path traversal attacks
    safe_path = os.path.realpath(os.path.join(OUTPUT_DIR, filename))
    if not safe_path.startswith(os.path.realpath(OUTPUT_DIR) + os.sep):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    return FileResponse(safe_path)
```

---

### SEC-04 — SQL INJECTION VIA UNPARAMETERISED QUERY IN MAIL ROUTES (HIGH)
**File:** `app/mail_agent/mail_routes.py` line 234  
**Problem:** A raw f-string SQL query is used when building the `DELETE` statement inside `run_cleanup_loop`. While `uid_str` is built from integer UIDs, this pattern is fragile. More dangerously, the `WHERE imap_uid IN (...)` inside `mail_agent.py` line 734 is an unparameterised f-string:

```python
await db_conn.execute(f"UPDATE emails SET status = 'Deleted' WHERE imap_uid IN ({uid_str})")
```

**Fix:** Use `executemany` with parameterised queries:

```python
await db_conn.executemany(
    "UPDATE emails SET status = 'Deleted' WHERE imap_uid = ?",
    [(uid,) for uid in batch_uids]
)
```

Or use `aiosqlite` with proper placeholders:
```python
placeholders = ",".join("?" * len(batch_uids))
await db_conn.execute(
    f"UPDATE emails SET status = 'Deleted' WHERE imap_uid IN ({placeholders})",
    batch_uids
)
```

---

### SEC-05 — SHELL INJECTION IN CODING AGENT (HIGH)
**File:** `app/backends/coding_agent.py` lines 108-115  
**Problem:** The `tool_run_command` function runs a user-supplied shell command with `shell=True`. Even with the blocklist regex patterns, a motivated attacker can bypass simple regex filters. The blocklist approach is fundamentally unreliable for sandboxing.

```python
res = subprocess.run(
    command,
    shell=True,    # ← DANGEROUS with untrusted input
    cwd=WORKSPACE_ROOT,
    ...
)
```

**Fix:** 
1. Use `shlex.split()` and pass a list (not a string) to `subprocess.run` — removes `shell=True`
2. Add an allowlist of permitted commands instead of a blocklist
3. Consider using `subprocess.run` with `shell=False` and a parsed arg list

```python
import shlex

def tool_run_command(command: str) -> str:
    # ... (security audit first) ...
    
    # Parse command safely — never use shell=True with untrusted input
    try:
        cmd_parts = shlex.split(command)
    except ValueError as e:
        return f"Error: Invalid command syntax: {e}"
    
    # Allowlist of permitted base commands
    ALLOWED_COMMANDS = {"python", "python3", "pip", "ls", "cat", "echo", "git", "pytest"}
    if not cmd_parts or cmd_parts[0] not in ALLOWED_COMMANDS:
        return f"Error: Command '{cmd_parts[0] if cmd_parts else ''}' is not in the allowed command list."
    
    try:
        res = subprocess.run(
            cmd_parts,       # ← list, not string
            shell=False,     # ← never shell=True
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=30
        )
        ...
```

---

### SEC-06 — HARDCODED WORKSPACE PATH IN CODING AGENT (MEDIUM)
**File:** `app/backends/coding_agent.py` line 11, `app/backends/security_scanner.py` line 9, `app/backends/mcp_agent.py` lines 91, 95  
**Problem:** Absolute paths to your home directory are hardcoded across multiple files:

```python
WORKSPACE_ROOT = "/home/pkkumar/AGGY/spark-test-tool"
```

This breaks portability, exposes the host filesystem structure, and is a maintenance burden.

**Fix:** Use environment variables:

```python
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

And add to `.env`:
```
WORKSPACE_ROOT=/home/pkkumar/AGGY/spark-test-tool
```

---

### SEC-07 — WEAK DEPENDENCY SECURITY SCANNER (MEDIUM)
**File:** `app/backends/security_scanner.py` lines 54-57  
**Problem:** The fallback dependency scanner only checks for 4 hardcoded malicious package names. This is trivially easy to bypass and provides false confidence:

```python
malicious_database = ["pep517-malicious", "request-logger-malicious", "discord-tokens-stealer", "browser-cookies-stealer"]
```

**Fix:** Replace with a real vulnerability scanner. Use `pip-audit` (a first-party Python tool by PyPA) as the fallback:

```python
def run_project_scan(target_path: str = WORKSPACE_ROOT) -> dict:
    # Try pip-audit for real CVE scanning
    try:
        res = subprocess.run(
            ["pip-audit", "--requirement", os.path.join(target_path, "requirements.txt"), "--format", "json"],
            capture_output=True, text=True, timeout=60
        )
        if res.returncode == 0:
            data = json.loads(res.stdout)
            vulns = data.get("vulnerabilities", [])
            if vulns:
                return {"status": "alert", "scanner": "pip-audit", "alerts": [v.get("description") for v in vulns]}
            return {"status": "clean", "scanner": "pip-audit"}
    except FileNotFoundError:
        logger.warning("pip-audit not found. Install with: pip install pip-audit")
    except Exception as e:
        logger.warning(f"pip-audit failed: {e}")
    ...
```

Add `pip-audit` to `requirements.txt`.

---

### SEC-08 — SSRF VULNERABILITY IN LINK EXTRACTION (MEDIUM)
**File:** `app/backends/extraction.py` lines 223-231, `app/backends/research_agent.py` lines 25-35  
**Problem:** The `extract_link` and `fetch_page` endpoints accept arbitrary URLs from the user body and make outbound HTTP requests without validation. An attacker can use this to:
- Scan your internal Docker network (e.g., `http://qdrant:6333`, `http://whisper-stt:9000`)
- Access cloud metadata services (e.g., `http://169.254.169.254/latest/meta-data/`)

**Fix:** Add a URL allowlist/blocklist and block private IP ranges:

```python
import ipaddress
from urllib.parse import urlparse

BLOCKED_HOSTS = {"169.254.169.254", "metadata.google.internal"}
BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
]

def is_safe_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname
        if host in BLOCKED_HOSTS:
            return False
        try:
            ip = ipaddress.ip_address(host)
            for net in BLOCKED_NETWORKS:
                if ip in net:
                    return False
        except ValueError:
            pass  # Hostname, not IP — allow (DNS resolves it)
        return True
    except Exception:
        return False
```

---

## 🟠 MODERNISATION ISSUES (June 2026)

### MOD-01 — DOCKER COMPOSE VERSION KEY IS DEPRECATED
**File:** `docker-compose.yml` line 1  
**Problem:** The `version: '3.8'` key has been deprecated since Docker Compose v2.x (now the default on all modern systems). It produces a warning and will be removed in future versions.

**Fix:** Remove the `version:` line entirely. Docker Compose v2 determines the format from the file structure.

```yaml
# REMOVE THIS LINE:
# version: '3.8'

services:
  gateway-app:
    ...
```

---

### MOD-02 — USING LATEST DOCKER IMAGE TAGS (ANTI-PATTERN)
**File:** `docker-compose.yml` lines 33, 53, 69  
**Problem:** `image: onerahmet/openai-whisper-asr-webservice:latest-gpu`, `image: climatologist/f5-tts:latest`, `image: qdrant/qdrant:latest` all use `:latest` tags. This causes non-reproducible builds — your production containers can silently change behaviour on a rebuild.

**Fix:** Pin to specific versions:

```yaml
whisper-stt:
  image: onerahmet/openai-whisper-asr-webservice:v1.7.0-gpu  # Check Docker Hub for current stable

f5-tts:
  image: climatologist/f5-tts:1.1.0  # Pin to tested version

qdrant:
  image: qdrant/qdrant:v1.11.0  # Pin to tested version
```

---

### MOD-03 — UNPINNED DEPENDENCIES IN requirements.txt (MEDIUM)
**File:** `requirements.txt`  
**Problem:** Many packages have no pinned version: `opencv-python-headless`, `deepface`, `ImageHash`, `tf-keras`, `Pillow`, `pypdf`, `pymupdf`, `yfinance`, `youtube-transcript-api`, `nltk`, `mcp`, `langfuse`. Unpinned packages mean a `pip install` in 6 months could install breaking versions.

**Fix:** Pin all packages with exact versions. Run `pip freeze > requirements.txt` in your working environment to capture exact versions. Example structure:

```txt
fastapi==0.115.0
uvicorn==0.32.0
httpx==0.28.0
python-multipart==0.0.18
python-dotenv==1.1.0
opencv-python-headless==4.10.0.84
deepface==0.0.93
ImageHash==4.3.1
tf-keras==2.17.0
duckduckgo_search==6.2.4
Pillow==10.4.0
pypdf==5.0.1
pymupdf==1.24.10
yfinance==0.2.44
youtube-transcript-api==0.6.2
aiosqlite==0.20.0
nltk==3.9.1
mcp==1.2.0
langfuse==2.55.0
pip-audit==2.7.3
```

---

### MOD-04 — DEPRECATED OLLAMA EMBEDDINGS ENDPOINT
**File:** `app/backends/rag.py` line 28  
**Problem:** The code uses `/api/embeddings` with a `prompt` field — this is the old Ollama API (pre-v0.5). Modern Ollama (v0.5+, current as of 2026) uses `/api/embed` with an `input` field, and the old endpoint is deprecated.

```python
r = await client.post(
    f"{OLLAMA_URL}/api/embeddings",    # ← deprecated endpoint
    json={"model": "nomic-embed-text:v1.5", "prompt": text}   # ← old field name
)
```

**Fix:** Update to modern endpoint and handle both single/batch:

```python
r = await client.post(
    f"{OLLAMA_URL}/api/embed",           # ← new endpoint
    json={"model": "nomic-embed-text:v1.5", "input": text}    # ← new field
)
# Response format: {"embeddings": [[...]]}
if r.status_code != 200:
    raise Exception(f"Ollama embed API returned status {r.status_code}: {r.text}")
res = r.json()
embeddings = res.get("embeddings", [])
if embeddings:
    return embeddings[0]
raise Exception("No embeddings found in Ollama response")
```

---

### MOD-05 — CUDA BASE IMAGE IS OUTDATED
**File:** `Dockerfile` line 1  
**Problem:** `FROM nvidia/cuda:12.2.2-base-ubuntu22.04` — CUDA 12.2 was released in mid-2023. As of June 2026, CUDA 12.6.x is current. Ubuntu 22.04 reaches EOL in April 2027. The `nvidia-utils-535` driver package is outdated (current is ~570+).

**Fix:** Update to a more recent base:

```dockerfile
FROM nvidia/cuda:12.6.2-base-ubuntu24.04

RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    nvidia-utils-565 \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    git \
    curl \
    && ln -s /usr/bin/python3.12 /usr/bin/python \
    && rm -rf /var/lib/apt/lists/*
```

---

### MOD-06 — RUNNING AS ROOT IN DOCKER (SECURITY + MODERNISATION)
**File:** `Dockerfile`  
**Problem:** The container runs as root by default. Best practice since 2024+ is to run as a non-root user.

**Fix:** Add a non-root user to the Dockerfile:

```dockerfile
# After WORKDIR /app ...
RUN useradd -m -u 1001 spark && chown -R spark:spark /app
USER spark
```

Also update the `CMD` to ensure the output directory is writable for this user.

---

### MOD-07 — DUPLICATE IMPORTS IN mcp_agent.py
**File:** `app/backends/mcp_agent.py` lines 1-16  
**Problem:** The entire import block is duplicated — `os`, `logging`, `json`, `httpx`, `re` are all imported twice, and `logger` is defined twice (lines 8 and 26). Python silently takes the second definition, but this is dead code and a maintenance hazard.

**Fix:** Remove lines 1-8 (the first duplicate block) and keep only the complete imports in lines 10-26.

---

### MOD-08 — YOUTUBE EXTRACTION IS A STUB / MOCK
**File:** `app/backends/extraction.py` lines 283-305  
**Problem:** The `extract_youtube` function is fake — it contains hardcoded fake transcript text and simulates processing with `asyncio.sleep(2.0)`. The `youtube-transcript-api` package is listed in `requirements.txt` but never actually used.

```python
text = f"# YouTube Transcript for {youtube_url}\n\n[00:01] Welcome to the Spark Media Factory workstation tutorial...\n"
```

**Fix:** Actually implement it using the installed package:

```python
async def extract_youtube(youtube_url: str):
    job_id = f"yt_{uuid.uuid4().hex[:8]}"
    logger.info(f"Extracting YouTube transcript for {youtube_url}")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
        import re as _re
        
        # Extract video ID from URL
        vid_match = _re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", youtube_url)
        if not vid_match:
            raise HTTPException(status_code=400, detail="Could not extract YouTube video ID from URL")
        
        video_id = vid_match.group(1)
        
        # Fetch transcript in a thread (synchronous library)
        transcript_list = await asyncio.to_thread(
            YouTubeTranscriptApi.get_transcript, video_id
        )
        
        lines = [f"[{int(entry['start'])//60:02d}:{int(entry['start'])%60:02d}] {entry['text']}" for entry in transcript_list]
        text = f"# YouTube Transcript\nURL: {youtube_url}\n\n" + "\n".join(lines)
        
        filename = f"{job_id}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        
        return {
            "text": text,
            "details": f"Fetched {len(transcript_list)} transcript entries.",
            "output_url": f"/output/{filename}",
            "filename": filename
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### MOD-09 — REPEATED `httpx.AsyncClient` IMPORTS IN HEALTH CHECK
**File:** `app/main.py` lines 97, 104, 112, 120  
**Problem:** `import httpx` is called inside each `try` block of the health check function 4 times. Python caches module imports so this doesn't actually re-import, but it is ugly and misleading code. `httpx` is already imported at the top of the module.

**Fix:** Remove the redundant per-block imports. Use the single shared `httpx` already imported at module level.

```python
# BEFORE (repeated 4 times inside health_check):
try:
    import httpx
    async with httpx.AsyncClient(timeout=3.0) as client:
        ...

# AFTER (clean — httpx already imported at top):
try:
    async with httpx.AsyncClient(timeout=3.0) as client:
        ...
```

---

### MOD-10 — HEALTH CHECK SHOULD USE PARALLEL REQUESTS
**File:** `app/main.py` lines 92-128  
**Problem:** The health check pings 4 services sequentially. Each has a 3-second timeout, so the worst case is a 12-second health check response. In a container orchestration environment (k8s, Docker healthcheck), this causes false-positive unhealthy states.

**Fix:** Use `asyncio.gather` to run all health checks in parallel:

```python
@app.get("/health")
async def health_check():
    async def check(name: str, url: str) -> tuple[str, str]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                r = await client.get(url)
                return name, "online" if r.status_code == 200 else "error"
        except Exception:
            return name, "offline"

    results = await asyncio.gather(
        check("ollama", f"{OLLAMA_URL}/api/tags"),
        check("comfyui", f"{COMFYUI_URL}/system_stats"),
        check("whisper", f"{WHISPER_URL}/docs"),
        check("f5tts", f"{F5_TTS_URL}/"),
    )
    services = {"gateway": "online"} | dict(results)
    return {"status": "online", "services": services}
```

---

### MOD-11 — NO REQUEST SIZE LIMITING (MEDIUM)
**File:** `app/main.py`  
**Problem:** There is no limit on request body size. A malicious actor could send a multi-gigabyte request body to `/api/rag/ingest`, `/api/extract/pdf`, etc. and cause out-of-memory conditions.

**Fix:** Add a request size middleware or use FastAPI's built-in `max_upload_size` parameter for file endpoints. For non-file endpoints, add a middleware:

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class LimitRequestSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_size: int = 100 * 1024 * 1024):  # 100MB
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next):
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.max_body_size:
                return Response("Request body too large", status_code=413)
        return await call_next(request)

app.add_middleware(LimitRequestSizeMiddleware)
```

---

### MOD-12 — NO API AUTHENTICATION / RATE LIMITING
**File:** `app/main.py`  
**Problem:** Every API endpoint is completely open — no authentication, no rate limiting. For a local tool this may be acceptable, but when port 5050 is exposed (even on `localhost`), any process or browser tab on the same machine has full access. The Coding Agent endpoint in particular can read/write/execute code.

**Fix:** Add at minimum a simple API key check for sensitive endpoints, and use `slowapi` for rate limiting:

```python
# Add to requirements.txt: slowapi==0.1.9
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to sensitive endpoints
@app.post("/api/gems/coding-agent")
@limiter.limit("10/minute")  # Max 10 coding agent calls per minute per IP
async def gems_coding_agent(request: Request):
    ...
```

For an API key:
```python
from fastapi.security import APIKeyHeader
from fastapi import Security, Depends

API_KEY = os.getenv("SPARK_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: str = Security(api_key_header)):
    if API_KEY and key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# Then add to protected routes:
@app.post("/api/gems/coding-agent", dependencies=[Depends(verify_api_key)])
```

---

## 🟡 CODE QUALITY IMPROVEMENTS

### QA-01 — REQUEST VALIDATION USES RAW `request.json()` INSTEAD OF PYDANTIC
**Files:** Most endpoints in `app/main.py`, `app/backends/*.py`  
**Problem:** Nearly every POST endpoint manually calls `body = await request.json()` and does `body.get(...)` with no type validation. This means:
- Malformed types (e.g., sending a string where an int is expected) silently fail
- No automatic OpenAPI docs schema for request bodies
- Difficult to maintain and test

**Fix:** Define Pydantic request models for all endpoints. Example for the chat endpoint:

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: str = Field(default="qwen3.6:27b")
    system_prompt: str = "You are a helpful AI assistant."
    rag: bool = False

@app.post("/api/text/chat")
async def text_chat(req: ChatRequest):
    return await ollama.chat_from_model(req, OLLAMA_URL)
```

---

### QA-02 — RESEARCH AGENT MODEL SELECTION IS DUPLICATED ACROSS FILES
**Files:** `app/backends/research_agent.py` lines 194-206, `app/backends/mcp_agent.py` lines 233-244  
**Problem:** Both files contain an identical model selection block (fetch `/api/tags`, prefer `qwen3:14b`, then `qwen3:8b`, then first available). This logic is duplicated verbatim.

**Fix:** Extract into a shared utility function in a new file `app/backends/utils.py`:

```python
# app/backends/utils.py
import httpx

async def resolve_best_model(ollama_url: str, preferred: list[str] = None) -> str:
    """Resolve the best available Ollama model from a preference list."""
    preferred = preferred or ["qwen3:14b", "qwen3:8b"]
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{ollama_url}/api/tags")
            if r.status_code == 200:
                available = [m["name"] for m in r.json().get("models", [])]
                for p in preferred:
                    if p in available:
                        return p
                if available:
                    return available[0]
    except Exception:
        pass
    return preferred[-1] if preferred else "qwen3:8b"
```

---

### QA-03 — CLASSIFY_HEURISTIC IS OVERLY SIMPLISTIC AND HAS A BUG
**File:** `app/mail_agent/mail_agent.py` lines 72-101  
**Problem:** 
1. The word `"off"` in the marketing keyword list matches almost every email subject with "off" in it (e.g., "Microsoft Teams is offline", "Your account payment is off schedule")
2. The word `"inside"` matches newsletters — but "Inside Sales" meeting email would be mis-categorised as Newsletter
3. The heuristic is a simple string `in` check, not word-boundary matching

**Fix:**
```python
# Use word-boundary matching with regex for subject keywords
import re as _re

def classify_heuristic(sender: str, subject: str) -> str:
    sender_lower = (sender or "").lower()
    subj_lower = (subject or "").lower()
    
    def keyword_in_subject(keyword: str) -> bool:
        # Word-boundary matching to avoid false positives
        return bool(_re.search(rf'\b{_re.escape(keyword)}\b', subj_lower))
    
    # ... check social domains ...
    # Remove "off", "inside" and "read" from keyword lists
    # Add whole-word check for subject keywords
    marketing_subject_keywords = ["discount", "free", "save", "sale", "order", "invoice", "receipt", "alert", "deal"]
    if any(keyword_in_subject(k) for k in marketing_subject_keywords):
        return "Marketing"
    ...
```

---

### QA-04 — SYNC STATUS IS A GLOBAL SINGLETON WITH RACE CONDITIONS
**File:** `app/mail_agent/mail_agent.py` lines 20-43  
**Problem:** `MailSyncStatus` is a module-level singleton. Concurrent requests (e.g., two users clicking sync simultaneously) can race to update `is_running`, `status`, etc., since there's no async lock. FastAPI is async and multiple coroutines can interleave.

**Fix:** Add an `asyncio.Lock` to protect state transitions:

```python
import asyncio

class MailSyncStatus:
    def __init__(self):
        self._lock = asyncio.Lock()
        # ... rest of __init__ ...
    
    async def try_acquire_lock(self) -> bool:
        """Returns True if we acquired the lock (i.e., no sync is running)."""
        async with self._lock:
            if self.is_running:
                return False
            self.is_running = True
            return True
```

---

### QA-05 — CODING AGENT WORKSPACE PATH IS HARDCODED INSIDE CONTAINER vs. HOST
**File:** `app/backends/coding_agent.py` line 11  
**Problem:** `WORKSPACE_ROOT = "/home/pkkumar/AGGY/spark-test-tool"` is a HOST path. Inside Docker, this path doesn't exist (the app is mounted at `/app`). The path validation `is_safe_path` will always fail or behave incorrectly inside the container.

**Fix:** Detect environment:

```python
# Use /app inside Docker, fall back to env var or detect from file location
WORKSPACE_ROOT = os.getenv(
    "WORKSPACE_ROOT",
    "/app" if os.path.exists("/app/app/main.py") else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
```

---

### QA-06 — KEYWORD SEARCH IN RAG SCROLLS ENTIRE DATABASE (PERFORMANCE)
**File:** `app/backends/rag.py` lines 337-376  
**Problem:** `keyword_query` scrolls ALL 10,000+ points from Qdrant just to do a Python-side `str in str` check. As the RAG database grows, this will become very slow and memory-intensive.

**Fix:** Use Qdrant's native payload filter instead. Qdrant supports full-text search on payload fields since v1.1:

```python
async def keyword_query(search_text: str, limit: int = 3) -> list:
    await ensure_collection()
    # Use Qdrant's payload text match filter
    payload = {
        "filter": {
            "must": [
                {
                    "key": "text",
                    "match": {
                        "text": search_text  # Qdrant full-text match
                    }
                }
            ]
        },
        "limit": limit,
        "with_payload": True,
        "with_vector": False
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/scroll",
                json=payload
            )
            ...
```

Note: Requires Qdrant collection to be created with a text index on the `text` field.

---

### QA-07 — RAG INGEST WRITES TEMP FILE TO /tmp INSIDE DOCKER (RAGFLOW PATH)
**File:** `app/backends/rag.py` lines 163-165  
**Problem:** RAGFlow ingestion writes a temp file to `/tmp`:
```python
temp_path = os.path.join("/tmp", temp_filename)
```
Inside Docker, `/tmp` is ephemeral and may not be writable with a non-root user. Use Python's `tempfile` module instead:

**Fix:**
```python
import tempfile

with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp_file:
    tmp_file.write(text)
    temp_path = tmp_file.name

try:
    # ... use temp_path ...
finally:
    if os.path.exists(temp_path):
        os.unlink(temp_path)
```

---

### QA-08 — MISSING `.gitignore` FILE
**Problem:** There is no `.gitignore` in the project root. This likely means `__pycache__`, `.env`, `output/`, `qdrant_storage/`, `cache/`, and `scratch/` directories are all tracked by git (or would be if this were committed).

**Fix:** Create `.gitignore`:

```gitignore
# Secrets
.env

# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/

# Runtime outputs
output/
qdrant_storage/
cache/
scratch/
docker_up.log

# IDEs
.idea/
.vscode/
*.swp
```

---

### QA-09 — RESEARCH AGENT USER AGENT STRING IS OUTDATED (2023)
**File:** `app/backends/extraction.py` line 229, `app/backends/research_agent.py` line 40  
**Problem:** The User-Agent string is `Chrome/115.0.0.0` — a browser version from 2023. Many modern websites check User-Agent and may block or rate-limit requests from outdated browser strings. Chrome is at 126+ as of mid-2026.

**Fix:** Update to a current User-Agent:
```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}
```

---

### QA-10 — NO STRUCTURED LOGGING (JSON FORMAT)
**File:** `app/main.py` lines 19-23  
**Problem:** Logs are emitted in plain text format. In a containerised/cloud environment (especially when logs are collected by Fluent Bit, Datadog, CloudWatch, etc.), structured JSON logging is expected and enables filtering, alerting, and dashboards.

**Fix:** Replace the basic logging config with JSON structured logging using `python-json-logger`:

```python
# Add to requirements.txt: python-json-logger==2.0.7
from pythonjsonlogger import jsonlogger

def setup_logging():
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[handler])

setup_logging()
```

---

### QA-11 — PILLAR NUMBERING COMMENTS ARE INCONSISTENT
**File:** `app/main.py` lines 167-220  
**Problem:** The pillar comments in the route file are inconsistently numbered:
```
PILLAR 2: TEXT
PILLAR 3: IMAGE
PILLAR 1: VIDEO   ← Out of order!
PILLAR 5: AUDIO
PILLAR 4: 3D
PILLAR 6: MUSIC
PILLAR 8: POST PROCESSING
PILLAR 7: EXTRACTION
PILLAR 9: RAG
```

This is cosmetic but makes the code misleading when reviewing routes. **Fix:** Renumber sequentially 1-9 in logical order (text → image → video → audio → 3D → music → extraction → RAG → postprocess).

---

### QA-12 — ASYNCIO GATHER TASKS NOT CANCELLED ON SHUTDOWN
**File:** `app/mail_agent/mail_agent.py` lines 44, 787-791  
**Problem:** Background tasks are added to `_active_sync_tasks` and `_purge_workers`, but there is no graceful shutdown handler to cancel them when the FastAPI app stops. This can cause `asyncio` to log `Task was destroyed but it is pending` errors during container shutdown.

**Fix:** Add a shutdown handler in the FastAPI lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Spark Test Tool gateway starting...")
    yield
    logger.info("Shutting down — cancelling active background tasks...")
    from app.mail_agent.mail_agent import _active_sync_tasks
    for task in list(_active_sync_tasks):
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    logger.info("Spark Test Tool gateway shut down.")
```

---

## 🔵 ARCHITECTURAL IMPROVEMENTS

### ARCH-01 — ADD A `.env.example` TEMPLATE FILE
Create `/home/pkkumar/AGGY/spark-test-tool/.env.example` with all required keys but NO real values:

```bash
# Gateway Configuration
PORT=5050
HOST=0.0.0.0

# External Host Backends
OLLAMA_URL=http://host.docker.internal:11434
COMFYUI_URL=http://host.docker.internal:8188

# Isolated Container Backends
WHISPER_URL=http://whisper-stt:8000
F5_TTS_URL=http://f5-tts:8000

# Default Models
DEFAULT_LLM_MODEL=
DEFAULT_VISION_MODEL=
DEFAULT_EMBED_MODEL=nomic-embed-text:latest

# Optional: Search API Keys
# TAVILY_API_KEY=
# SEARXNG_URL=
# GOOGLE_API_KEY=
# GOOGLE_CSE_ID=

# Yahoo Mail (NEVER commit real credentials here)
YAHOO_EMAIL=
YAHOO_APP_PASSWORD=

# Security
SPARK_API_KEY=
ALLOWED_ORIGINS=http://localhost:5050

# Workspace (host path to project root)
WORKSPACE_ROOT=/home/youruser/spark-test-tool
```

---

### ARCH-02 — ADD DOCKERFILE HEALTHCHECK DIRECTIVE
**File:** `Dockerfile`  
**Problem:** Docker has no idea if the app is healthy — it only knows if the process is running. A healthcheck directive causes `docker ps` to show the real health state and allows Docker Compose to restart unhealthy containers.

**Fix:** Add to Dockerfile:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1
```

---

### ARCH-03 — ADD EXCEPTION HANDLERS FOR UNHANDLED ERRORS
**File:** `app/main.py`  
**Problem:** Unhandled exceptions in route handlers will return a 500 with the full Python traceback in the response body, which can leak internal details.

**Fix:** Add a global exception handler:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred."}  # Don't expose exc details
    )
```

---

### ARCH-04 — CONSIDER ADDING ASYNC LOCK FOR GPU OPERATIONS
**Problem:** Multiple concurrent requests to `/api/image/generate`, `/api/video/generate`, `/api/3d/generate` etc. will all simultaneously try to use the GPU via ComfyUI. ComfyUI has its own internal queue, but generating many concurrent requests can cause OOM on the GPU.

**Recommendation:** Add a simple asyncio semaphore to limit concurrent GPU-bound jobs:

```python
# In app/main.py
GPU_SEMAPHORE = asyncio.Semaphore(2)  # Max 2 concurrent GPU tasks

@app.post("/api/image/generate")
async def image_generate(request: Request):
    async with GPU_SEMAPHORE:
        return await comfyui_image.generate(request, COMFYUI_URL, OUTPUT_DIR)
```

---

## Summary Table

| ID | Severity | File | Issue |
|---|---|---|---|
| SEC-01 | 🔴 CRITICAL | `.env` / `Dockerfile` | Live Yahoo password in Docker image |
| SEC-02 | 🔴 HIGH | `main.py` | Wildcard CORS + credentials |
| SEC-03 | 🔴 HIGH | `main.py` | Path traversal in `/output/{filename}` |
| SEC-04 | 🔴 HIGH | `mail_agent.py` / `mail_routes.py` | Raw f-string SQL |
| SEC-05 | 🔴 HIGH | `coding_agent.py` | Shell injection via `shell=True` |
| SEC-06 | 🟠 MEDIUM | Multiple files | Hardcoded home directory path |
| SEC-07 | 🟠 MEDIUM | `security_scanner.py` | Toy malicious-package DB |
| SEC-08 | 🟠 MEDIUM | `extraction.py`, `research_agent.py` | SSRF via user-supplied URLs |
| MOD-01 | 🟡 LOW | `docker-compose.yml` | Deprecated `version:` key |
| MOD-02 | 🟠 MEDIUM | `docker-compose.yml` | `:latest` Docker tags |
| MOD-03 | 🟠 MEDIUM | `requirements.txt` | Unpinned dependencies |
| MOD-04 | 🟠 MEDIUM | `rag.py` | Deprecated Ollama `/api/embeddings` |
| MOD-05 | 🟡 LOW | `Dockerfile` | CUDA 12.2 + Ubuntu 22.04 outdated |
| MOD-06 | 🟠 MEDIUM | `Dockerfile` | Runs as root |
| MOD-07 | 🟡 LOW | `mcp_agent.py` | Duplicate import block |
| MOD-08 | 🟠 MEDIUM | `extraction.py` | YouTube extraction is a stub/mock |
| MOD-09 | 🟡 LOW | `main.py` | Repeated `import httpx` in health check |
| MOD-10 | 🟠 MEDIUM | `main.py` | Sequential health checks (slow) |
| MOD-11 | 🟠 MEDIUM | `main.py` | No request body size limit |
| MOD-12 | 🟠 MEDIUM | `main.py` | No authentication or rate limiting |
| QA-01 | 🟠 MEDIUM | Multiple | Raw `request.json()` instead of Pydantic |
| QA-02 | 🟡 LOW | `research_agent.py`, `mcp_agent.py` | Duplicated model selection code |
| QA-03 | 🟡 LOW | `mail_agent.py` | Heuristic classifier bugs |
| QA-04 | 🟠 MEDIUM | `mail_agent.py` | Race conditions in sync status |
| QA-05 | 🟠 MEDIUM | `coding_agent.py` | Host path wrong inside Docker |
| QA-06 | 🟠 MEDIUM | `rag.py` | Keyword search scans entire DB |
| QA-07 | 🟡 LOW | `rag.py` | `/tmp` usage inside Docker |
| QA-08 | 🟡 LOW | Root | No `.gitignore` |
| QA-09 | 🟡 LOW | Multiple | Outdated User-Agent string |
| QA-10 | 🟡 LOW | `main.py` | No structured/JSON logging |
| QA-11 | 🟡 LOW | `main.py` | Inconsistent pillar numbering |
| QA-12 | 🟡 LOW | `mail_agent.py` | Background tasks not cancelled on shutdown |
| ARCH-01 | 🟡 LOW | Root | No `.env.example` |
| ARCH-02 | 🟡 LOW | `Dockerfile` | No `HEALTHCHECK` directive |
| ARCH-03 | 🟡 LOW | `main.py` | No global exception handler |
| ARCH-04 | 🟡 LOW | `main.py` | No GPU concurrency limiting |

---

*End of review. Fix SEC-01 immediately — the email password is live and exposed.*
