# Known Issues & Setup Boundaries — docs/KNOWN_ISSUES.md

This registry tracks specific hardware limitations, configuration constraints, and known runtime gotchas for the Spark Media Workstation.

---

## 1. Directory & File Placement Constraints

> [!CRITICAL]
> **ComfyUI Text Encoders Path Restriction**
> All text encoder model checkpoints (specifically `t5xxl_fp8_e4m3fn.safetensors` and `clip_l.safetensors`) must remain located in the `/home/pkkumar/spark-factory/models/clip/` directory. They must **never** be moved or symlinked to the `models/text_encoders/` folder. The custom FLUX loader configurations within ComfyUI are hardcoded to scan the standard `clip` path; modifying this directory structure will break the image generation pipeline.

---

## 2. Hardware and Resource Gotchas

### CUDA Out-of-Memory (OOM) on Concurrent Models
- **Symptom:** Silent crash of ComfyUI or Ollama during generation.
- **Cause:** Running a 14B LLM model (like `qwen3:14b`) concurrently with heavy visual processing (like FLUX image or Wan2.2 video generation) on a single GPU.
- **Workaround:** Ensure the `GPU_SEMAPHORE` limit (configured in FastAPI) is respected. Route text chat LLMs to Node B's secondary GPU stack (RTX 3060 Ti/3060) to avoid overloading the RTX 3090.

### Whisper Container Cold Start Latency
- **Symptom:** The first `/api/audio/transcribe` request takes 30-60 seconds, or times out.
- **Cause:** The Whisper container (`faster-whisper` engine) dynamically downloads or loads the `large-v3` weights into VRAM on the first invocation.
- **Workaround:** Run a warm-up transcription query during startup or pre-load the model cache.

### NLTK parser download requirement on first run
- **Symptom:** Text extraction / RAG returns `LookupError` for `punkt` or `punkt_tab` on startup.
- **Cause:** NLTK chunking requires specific tokenizer data packages that are downloaded dynamically at runtime if missing.
- **Workaround:** The gateway includes automatic fallback downloads, but an offline environment will require pre-packaging the `nltk_data` folder in the container image.

---

## 3. Operations & Environment Issues

### `host.docker.internal` DNS Resolution Failures
- **Symptom:** Gateway container fails to connect to Ollama or ComfyUI, logging `Name or service not known`.
- **Cause:** Some Linux distributions/kernels do not automatically resolve the Docker bridge gateway IP via `host.docker.internal`.
- **Workaround:** The container uses the `extra_hosts` option mapping `host.docker.internal:host-gateway` in `docker-compose.yml`. Ensure the Docker daemon has user namespaces/iptables configured correctly.

### Volume Mount Permissions for `/comfyui-output:ro`
- **Symptom:** Gateway logs permission errors when trying to read generated files from ComfyUI output.
- **Cause:** Host permissions on `/home/pkkumar/spark-factory/ComfyUI/output` do not align with the Gateway container's non-root execution user.
- **Workaround:** Ensure directory read permissions are set to `755` on the host, allowing the container's read-only mount (`:ro`) to access generated assets.

### SQLite WAL Mode Concurrency Limits
- **Symptom:** `aiosqlite.OperationalError: database is locked` during high concurrent job updates.
- **Cause:** High-frequency transaction commits to `jobs.db` or `emails.db` exceeding SQLite WAL concurrency bounds.
- **Workaround:** Both `job_store.py` and `mail_routes.py` initialize databases using `PRAGMA journal_mode=WAL;` and utilize async locks to serialize SQLite writes.

---

## 4. External Services & APIs

### SearXNG / Web Search Rate Limiting
- **Symptom:** The Research Agent returns empty queries or HTTP 403/429 errors.
- **Cause:** Public SearXNG engines or downstream search engines (Google/Bing) block search traffic coming from local coordinator IPs.
- **Workaround:** Fall back to DuckDuckGo search or configure dedicated `TAVILY_API_KEY` credentials in the `.env` file to bypass rate-limiting.
