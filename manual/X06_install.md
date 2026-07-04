---
chapter_id: X06
title: "Install & Version Pinning"
layer: "Foundation"
status: "implemented"
purpose: "Ensure reproducible builds with pinned dependencies and Docker configuration"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "20m"
inputs:
  - "Docker installed"
  - "Python 3.12+"
outputs:
  - "Built Docker image"
  - "Pinned requirements"
  - "Reproducible environment"
qc_gates:
  - "Docker image builds successfully"
  - "All dependencies pinned"
  - "Health check passes"
default_tools:
  primary: "Docker + pip"
  fallback: "Manual installation"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X06"
  run: "run_X06"
  score: "score_X06"
  retry: "retry_X06"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X06 — Install & Version Pinning

## Chapter Card
**Chapter:** `X06 — Install & Version Pinning`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Ensure reproducible builds with pinned dependencies and Docker configuration.  
**Last Verified:** 2026-06-15

**What Exists:**
- ✅ Dockerfile with pinned base image (`nvidia/cuda:12.6.2-base-ubuntu24.04`)
- ✅ `requirements.txt` with pinned python packages
- ✅ Docker Compose service stack building dynamically via `start.sh`

---

## 1) Quickstart (Golden Path)

### Goal
Build and run the Spark Media Factory from scratch.

### Prerequisites
- Docker Desktop or Docker Engine 20.10+
- Docker Compose v2
- NVIDIA Container Toolkit (for GPU support)

### Golden Path Steps

**Step 1 — Clone Repository**
```bash
git clone <repository-url>
cd spark-test-tool
```

**Step 2 — Configure Environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

**Step 3 — Build and Start**
```bash
chmod +x start.sh
./start.sh
```

OR manually:
```bash
docker compose up --build -d
```

**Step 4 — Verify Installation**
```bash
docker compose ps
curl http://localhost:5050/health
```

---

## 2) Dockerfile Analysis

### Base Image
```dockerfile
FROM nvidia/cuda:12.6.2-base-ubuntu24.04
```
- **CUDA:** 12.6.2
- **Ubuntu:** 24.04 LTS
- **Purpose:** GPU support for inference

### System Dependencies
```dockerfile
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3.12-dev \
    nvidia-utils-565 \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    git \
    curl
```

### Security
```dockerfile
RUN useradd -m -u 1001 spark && chown -R spark:spark /app
USER spark
```
- Runs as non-root user `spark` (UID 1001)

### Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1
```

---

## 3) Python Dependencies

### Pinned Versions
| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | 0.115.0 | Web framework |
| `uvicorn` | 0.32.0 | ASGI server |
| `httpx` | 0.28.0 | HTTP client |
| `aiosqlite` | 0.20.0 | Async SQLite |
| `nltk` | 3.9.1 | NLP tokenization |
| `duckduckgo_search` | 6.2.4 | Web search |
| `langfuse` | 2.55.0 | Telemetry |
| `pip-audit` | 2.7.3 | Security scanning |

### Dependency Categories
- **Web Framework:** FastAPI, Uvicorn
- **HTTP Client:** httpx
- **Data:** aiosqlite, numpy, pandas
- **CV/Image:** opencv, deepface, Pillow
- **PDF:** pypdf, pymupdf
- **NLP:** nltk, duckduckgo_search
- **AI/LLM:** mcp, langfuse
- **Security:** pip-audit

---

## 4) Version Pinning Strategy

### What's Pinned
- ✅ All direct dependencies in `requirements.txt`
- ✅ Docker base image tag (`nvidia/cuda:12.6.2-base-ubuntu24.04`)
- ✅ Python version (3.12)

### What's Not Pinned
- ❌ Transitive dependencies (no lock file)
- ❌ Docker Compose service images (use `latest`)
- ❌ Ollama models (versioned by tag)

### Recommendations
1. **Add `pip-compile`** to generate `requirements.lock`
2. **Pin Docker Compose images** to specific tags
3. **Automate dependency updates** with Dependabot or Renovate

---

## 5) Troubleshooting

### Issue 1 — "Docker build fails"
- **Cause:** Network issue or missing dependency
- **Fix:** Check internet, verify Dockerfile syntax
- **Prevention:** Test build locally first

### Issue 2 — "pip install fails"
- **Cause:** Package version conflict
- **Fix:** Check package compatibility, update pins
- **Prevention:** Use virtual environment for testing

### Issue 3 — "CUDA not available"
- **Cause:** NVIDIA Container Toolkit not installed
- **Fix:** Install nvidia-docker2
- **Prevention:** Verify with `docker run --gpus all nvidia/cuda:11.0-base nvidia-smi`

### Issue 4 — "Health check fails"
- **Cause:** Application not starting
- **Fix:** Check container logs with `docker logs spark-gateway`
- **Prevention:** Verify all dependencies installed

---

## 6) Change Log

- 2026-06-15 — Documented actual Dockerfile and requirements
- 2025-12-24 — Original template created