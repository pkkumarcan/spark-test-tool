---
chapter_id: X01
title: "Orientation & Quickstart"
layer: "Foundation"
status: "implemented"
purpose: "Get the Spark Media Factory running and verify first end-to-end job"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - "Docker installed"
  - "NVIDIA GPU with drivers"
  - "Ollama running on host"
outputs:
  - "Running gateway at http://localhost:5050"
  - "Health check passing"
  - "First generated asset"
qc_gates:
  - "All Docker containers running"
  - "GET /health returns online"
  - "Web UI accessible"
default_tools:
  primary: "Docker Compose + start.sh"
  fallback: "Manual docker commands"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X01"
  run: "run_X01"
  score: "score_X01"
  retry: "retry_X01"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X01 — Orientation & Quickstart

## Chapter Card
**Chapter:** `X01 — Orientation & Quickstart`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Get the Spark Media Factory running and verify first end-to-end job.  
**Last Verified:** 2026-06-15  

**Inputs:**
- Docker Engine or Desktop
- NVIDIA Driver + Container Toolkit
- Ollama running on host port 11434

**Outputs:**
- Gateway web app running at `http://localhost:5050`
- Integrated background workers active in container network

**Quality Gates (must pass):**
- `All Docker containers running == True`
- `GET /health` returns status online
- Web UI accessible in browser

**Default tools:**
- `Docker Compose + start.sh` (primary setup coordinator)
- `run_smoke_tests.py` (primary automated onboarding verification)

**Automation hooks:**
- `validate_X01(job_id)`
- `run_X01(job_id, profile)`
- `score_X01(job_id)`
- `retry_X01(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Start the Spark Media Factory and generate your first asset.

### Prerequisites
- Docker Desktop or Docker Engine installed
- NVIDIA GPU with drivers + NVIDIA Container Toolkit
- Ollama installed and running (`ollama serve`)
- At least one model pulled (`ollama pull gemma4:12b-it-qat`)

### Golden Path Steps

**Step 1 — Start Ollama (if not running)**
```bash
# Terminal 1: Start Ollama
ollama serve

# Verify it's running
curl http://localhost:11434/api/tags
```
Expected: List of available models

**Step 2 — Start the Factory**
```bash
# From project root
chmod +x start.sh
./start.sh
```
OR manually:
```bash
docker compose up --build -d
```

**Step 3 — Verify Services and Run Automated Verification**
To run the automated prerequisite check and smoke test suite:
```bash
python run_smoke_tests.py
```
Expected: Markdown report printed indicating all routes `/health`, `/api/gpu/status`, `/api/text/models` are returning `PASS`.

**Step 4 — Access Web UI**
Open browser to `http://localhost:5050`

**Step 5 — Generate First Image**
In the web UI:
1. Select "Image" tab
2. Enter prompt: "A simple red circle on white background"
3. Click "Generate"
4. Wait for result

### Done looks like
- [ ] All 4 Docker containers running
- [ ] Health check returns `{"status": "online"}`
- [ ] Web UI loads in browser
- [ ] First image generated successfully
- [ ] Smoke test report generated: `smoke_test_report.md`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Docker | Installed | Docker Engine or Desktop |
| NVIDIA drivers | Installed | For GPU passthrough |
| NVIDIA Container Toolkit | Installed | For Docker GPU access |
| Ollama | Running | LLM inference server |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Gateway | `http://localhost:5050` | FastAPI application |
| Health | `GET /health` | Service status |
| Web UI | Browser | Glassmorphic interface |

### Definition of Done (DoD)
All services running + health check passing + first asset generated.

---

## 3) Directory Structure

```
spark-test-tool/
├── .env                    # Environment variables
├── .spark_coder/           # Agent memory
│   └── MEMORY.md
├── app/                    # Application code
│   ├── backends/           # AI pipelines
│   ├── data/               # Reference docs
│   ├── mail_agent/         # Email integration
│   ├── static/             # Frontend files
│   └── main.py             # FastAPI entry point
├── manual/                 # Documentation
├── output/                 # Generated assets
├── docker-compose.yml      # Service definitions
├── Dockerfile              # Gateway image
├── requirements.txt        # Python dependencies
├── start.sh                # Startup script
└── run_smoke_tests.py      # Verification suite
```

---

## 4) Service Map

| Service | Port | Container | Purpose |
|---------|------|-----------|---------|
| Gateway | 5050 | spark-gateway | FastAPI app |
| Ollama | 11434 | Host process | LLM inference |
| ComfyUI | 8188 | Host process | Image/video gen |
| Whisper | 8010 | spark-whisper | Speech-to-text |
| F5-TTS | 8020 | spark-f5tts | Text-to-speech |
| Qdrant | 6333 | spark-qdrant | Vector database |

---

## 5) Troubleshooting

### Issue 1 — "Docker compose fails to start"
- **Cause:** Port conflict or missing dependency
- **Fix:** Check port availability, verify Docker running
- **Prevention:** Run `docker compose config` to validate

### Issue 2 — "GPU not available in container"
- **Cause:** NVIDIA Container Toolkit not installed
- **Fix:** Install nvidia-docker2, restart Docker
- **Prevention:** Run `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`

### Issue 3 — "Cannot connect to Ollama"
- **Cause:** Ollama not running on host
- **Fix:** Run `ollama serve` in separate terminal
- **Prevention:** Add to startup script

### Issue 4 — "Health check fails"
- **Cause:** Service not responding
- **Fix:** Check container logs with `docker logs spark-gateway`
- **Prevention:** Wait for services to fully start

---

## 6) Change Log

- 2026-06-15 — Documented actual startup process and integrated run_smoke_tests.py validation.