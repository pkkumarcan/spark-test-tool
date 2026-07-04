---
chapter_id: X10
title: "Reliability Basics"
layer: "Foundation"
status: "implemented"
purpose: "Handle failures gracefully with rollback rules and common failure modes"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "15m"
inputs:
  - "System logs"
  - "Error reports"
outputs:
  - "Rollback playbook"
  - "Failure mode index"
  - "Recovery procedures"
qc_gates:
  - "Error handling in place"
  - "Rollback procedures documented"
  - "Common failures identified"
default_tools:
  primary: "Job store + error handling"
  fallback: "Manual recovery"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X10"
  run: "run_X10"
  score: "score_X10"
  retry: "retry_X10"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X10 — Reliability Basics

## Chapter Card
**Chapter:** `X10 — Reliability Basics`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Handle failures gracefully with rollback rules and common failure modes.  
**Last Verified:** 2026-06-15

**What Exists:**
- ✅ Global exception handler (`main.py:114-120`)
- ✅ Job failure tracking (`job_store.py`)
- ✅ Security scanner with rollback (`security_scanner.py`)
- ✅ Request size limit middleware
- ✅ Automatic restart policies (`restart: always` in `docker-compose.yml`)

---

## 1) Error Handling Architecture

### Global Exception Handler
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Check server logs for details."}
    )
```

### Request Size Limit
```python
class LimitRequestSizeMiddleware(BaseHTTPMiddleware):
    MAX_BODY = 200 * 1024 * 1024  # 200 MB
    
    async def dispatch(self, request: Request, call_next):
        cl = request.headers.get("content-length")
        if cl and int(cl) > self.MAX_BODY:
            return Response("Request body too large (max 200 MB)", status_code=413)
        return await call_next(request)
```

---

## 2) Common Failure Modes

### Service Failures
| Failure | Cause | Recovery |
|---------|-------|----------|
| Ollama unreachable | Host process crashed | Restart `ollama serve` |
| ComfyUI timeout | GPU overloaded | Wait, reduce concurrent tasks |
| Whisper error | Audio too long | Split audio, retry |
| F5-TTS error | Model loading | Wait for model load |
| Qdrant error | Container stopped | `docker compose restart qdrant` |

### Job Failures
| Failure | Cause | Recovery |
|---------|-------|----------|
| Job timeout | Task too long | Increase timeout, split task |
| GPU OOM | Insufficient VRAM | Reduce resolution/frames |
| Disk full | Output directory full | Clean old assets |
| Permission error | File access denied | Check permissions |

### Security Failures
| Failure | Cause | Recovery |
|---------|-------|----------|
| Malicious dependency | Tampered package | Rollback requirements.txt |
| Path traversal | Invalid file path | Block request, log attempt |
| Command injection | Dangerous command | Block command, alert user |

---

## 3) Rollback Procedures

### Requirements.txt Rollback
When `security_scanner` detects malicious changes:
```python
# Automatic rollback in tool_write_file
if is_req and audit.get("status") == "alert":
    # Restore original content
    with open(abs_path, 'w', encoding='utf-8') as f:
        f.write(old_content)
    return f"Error: Write blocked by security scanner."
```

### Job Rollback
```bash
# Cancel a running job
curl -X DELETE http://localhost:5050/api/jobs/{job_id}

# Clean up output files
rm /app/output/{job_id}.*
```

### Docker Rollback
```bash
# Stop all services
docker compose down

# Restart with previous image
docker compose up -d --force-recreate
```

---

## 4) Recovery Procedures

### Service Recovery
```bash
# Check service status
docker compose ps

# Restart specific service
docker compose restart gateway-app

# View logs
docker compose logs --tail 50 gateway-app

# Full restart
docker compose down && docker compose up -d
```

### Data Recovery
```bash
# Backup Qdrant
cp -r ./qdrant_storage ./qdrant_storage.backup

# Backup job database
cp /app/output/jobs.db /app/output/jobs.db.backup

# Restore from backup
cp ./qdrant_storage.backup ./qdrant_storage
```

---

## 5) Monitoring Checklist

### Daily
- [ ] Check `docker compose ps` for stopped containers
- [ ] Review `docker compose logs --tail 100` for errors
- [ ] Verify health check passing

### Weekly
- [ ] Clean old output files
- [ ] Check disk usage
- [ ] Review job failure rates

### Monthly
- [ ] Update Docker images
- [ ] Review security scanner alerts
- [ ] Test recovery procedures

---

## 6) Troubleshooting

### Issue 1 — "Service keeps crashing"
- **Cause:** Insufficient resources or bug
- **Fix:** Check logs, increase limits
- **Prevention:** Monitor resource usage

### Issue 2 — "Jobs stuck in 'running'"
- **Cause:** Process hung or crashed
- **Fix:** Cancel job, restart service
- **Prevention:** Implement timeouts

### Issue 3 — "Data corruption"
- **Cause:** Disk error or improper shutdown
- **Fix:** Restore from backup
- **Prevention:** Regular backups

### Issue 4 — "Security alert triggered"
- **Cause:** Malicious change detected
- **Fix:** Review alert, rollback if needed
- **Prevention:** Review all changes before commit

---

## 7) Change Log

- 2026-06-15 — Documented actual error handling and recovery
- 2025-12-24 — Original template created