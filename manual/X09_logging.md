---
chapter_id: X09
title: "Logging, Metrics & Observability"
layer: "Foundation"
status: "implemented"
purpose: "Track system performance, errors, and usage through logging and telemetry"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "15m"
inputs:
  - "Running system"
outputs:
  - "Structured logs"
  - "Telemetry traces"
  - "Job status records"
qc_gates:
  - "Logs captured for all requests"
  - "Errors tracked with context"
  - "Job progress visible"
default_tools:
  primary: "Python logging + Langfuse"
  fallback: "Console logs only"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X09"
  run: "run_X09"
  score: "score_X09"
  retry: "retry_X09"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X09 — Logging, Metrics & Observability

## Chapter Card
**Chapter:** `X09 — Logging, Metrics & Observability`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Track system performance, errors, and usage through logging and telemetry.  
**Last Verified:** 2026-06-15

**What Exists:**
- ✅ Python structured logging (`main.py:30-36`)
- ✅ Langfuse telemetry integration (`telemetry.py`)
- ✅ Job status tracking (`job_store.py`)
- ✅ GPU status endpoint (`GET /api/gpu/status`)
- ✅ Automated smoke test execution reporting (`run_smoke_tests.py`)

---

## 1) Logging Configuration

### Log Format
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
```

### Log Levels by Component
| Component | Level | Purpose |
|-----------|-------|---------|
| `spark.gateway` | INFO | Main application |
| `spark.backend.*` | INFO | Backend modules |
| `spark.job_store` | INFO | Job queue |

### Viewing Logs
```bash
# Docker Compose logs
docker compose logs -f

# Specific container
docker compose logs -f gateway-app

# Last 100 lines
docker compose logs --tail 100 gateway-app
```

---

## 2) Telemetry (Langfuse)

### Configuration
```bash
# .env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://host.docker.internal:3002
```

### What's Traced
- LLM generations (model, prompt, completion, latency)
- Tool executions
- Errors with context

### Trace Function
```python
from app.backends.telemetry import trace_generation

trace_generation(
    name="chat_completion",
    model="qwen3:8b",
    prompt=user_message,
    completion=assistant_response,
    latency_seconds=2.5
)
```

---

## 3) Job Status Tracking

### Job Store (SQLite)
- **Database:** `/app/output/jobs.db`
- **Mode:** WAL (Write-Ahead Logging)
- **Persistence:** Survives container restarts

### Job Lifecycle
```
pending → running → completed
                  → failed
                  → cancelled
```

### Job Fields
| Field | Type | Purpose |
|-------|------|---------|
| `job_id` | TEXT | Unique identifier |
| `job_type` | TEXT | Task type (e.g., "video_generate") |
| `status` | TEXT | Current status |
| `progress_pct` | INTEGER | Progress percentage |
| `progress_msg` | TEXT | Human-readable progress |
| `result` | TEXT | JSON result data |
| `error` | TEXT | Error message if failed |
| `created_at` | REAL | Creation timestamp |
| `updated_at` | REAL | Last update timestamp |

### Querying Jobs
```bash
# List recent jobs
curl http://localhost:5050/api/jobs

# Get specific job
curl http://localhost:5050/api/jobs/{job_id}

# Cancel job
curl -X DELETE http://localhost:5050/api/jobs/{job_id}
```

---

## 4) GPU Monitoring

### Endpoint
```bash
curl http://localhost:5050/api/gpu/status
```

### Response
```json
{
  "gpus": {
    "gpu0": {
      "index": 0,
      "name": "NVIDIA GeForce RTX 3060",
      "vram_used_mb": 8192,
      "vram_total_mb": 12288,
      "utilization_pct": 75,
      "temperature_c": 65,
      "power_w": 150.0
    }
  }
}
```

---

## 5) Metrics to Track

### System Metrics
- `request_count` — Total requests
- `request_latency` — Response time
- `error_rate` — Errors per request
- `gpu_utilization` — GPU usage percentage
- `gpu_vram_used` — VRAM consumption

### Job Metrics
- `job_duration` — Time to complete
- `job_success_rate` — Successful vs failed
- `queue_depth` — Pending jobs

### Business Metrics
- `generations_per_hour` — Throughput
- `model_usage` — Which models are used most
- `feature_usage` — Which tools are popular

---

## 6) Troubleshooting

### Issue 1 — "No logs appearing"
- **Cause:** Logging level too high
- **Fix:** Set `LOG_LEVEL=DEBUG` in `.env`
- **Prevention:** Use INFO level by default

### Issue 2 — "Langfuse not connecting"
- **Cause:** Langfuse server not running
- **Fix:** Start Langfuse or disable telemetry
- **Prevention:** Check Langfuse health

### Issue 3 — "Job status not updating"
- **Cause:** SQLite database locked
- **Fix:** Check file permissions, restart container
- **Prevention:** Use WAL mode (already configured)

### Issue 4 — "GPU stats unavailable"
- **Cause:** nvidia-smi not accessible
- **Fix:** Install nvidia-utils in container
- **Prevention:** Use NVIDIA base image

---

## 7) Change Log

- 2026-06-15 — Documented actual logging and telemetry setup
- 2025-12-24 — Original template created