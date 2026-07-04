---
chapter_id: X92
title: "Security & Access Control"
layer: "Governance"
status: "implemented"
purpose: "Protect the system with security scanning, access control, and best practices"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "15m"
inputs:
  - "System configuration"
  - "Security policies"
outputs:
  - "Security checklist"
  - "Access control rules"
  - "Incident response plan"
qc_gates:
  - "Security scanner active"
  - "Access controls in place"
  - "Secrets secured"
default_tools:
  primary: "security_scanner.py"
  fallback: "Manual review"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X92"
  run: "run_X92"
  score: "score_X92"
  retry: "retry_X92"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X92 — Security & Access Control

## Chapter Card
**Chapter:** `X92 — Security & Access Control`  
**Layer:** `Governance`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Protect the system with security scanning, access control, and best practices.  
**Last Verified:** 2026-06-15

**What Exists:**
- ✅ Security scanner (`security_scanner.py`)
- ✅ CORS configuration
- ✅ Request size limits
- ✅ Path traversal protection
- ✅ Non-root Docker user
- ✅ Bumblebee Agentic Security Sandbox command intercepts and blockers mapping to `ALLOWED_COMMANDS` in `coding_agent.py`

---

## 1) Security Features Implemented

### Security Scanner
**File:** `app/backends/security_scanner.py`

**Scanning Layers:**
1. **Bumblebee CLI** — Binary dependency scan
2. **pip-audit** — CVE vulnerability scan
3. **Static signatures** — Known malicious packages
4. **Command audit** — Block dangerous commands

### CORS Configuration
```bash
# .env
ALLOWED_ORIGINS=http://localhost:5050,http://127.0.0.1:5050
```

### Request Size Limit
```python
MAX_BODY = 200 * 1024 * 1024  # 200 MB
```

### Path Traversal Protection
```python
def is_safe_path(path: str) -> bool:
    abs_path = os.path.abspath(os.path.join(WORKSPACE_ROOT, path))
    return abs_path.startswith(os.path.abspath(WORKSPACE_ROOT))
```

### Command Allowlist
```python
ALLOWED_COMMANDS = {
    "python", "python3", "pip", "pip3",
    "ls", "cat", "echo", "head", "tail", "wc",
    "git", "pytest", "ruff", "black",
    "find", "grep", "diff",
}
```

---

## 2) Docker Security

### Non-Root User
```dockerfile
RUN useradd -m -u 1001 spark && chown -R spark:spark /app
USER spark
```

### Volume Mounts (Read-Only Where Possible)
```yaml
volumes:
  - /home/pkkumar/spark-factory/ComfyUI/output:/comfyui-output:ro
```

### Network Isolation
- Internal services use Docker DNS
- External services use `host.docker.internal`

---

## 3) Environment Security

### Secret Management
- `.env` file excluded from git (`.gitignore`)
- `.env.example` contains template with no real values
- Docker reads secrets via `env_file: .env`

### CORS Origins
```bash
# Default: localhost only
ALLOWED_ORIGINS=http://localhost:5050,http://127.0.0.1:5050

# For LAN access (add your LAN IP)
ALLOWED_ORIGINS=http://localhost:5050,http://192.168.1.100:5050
```

---

## 4) Security Checklist

### Before Deployment
- [ ] `.env` contains no real secrets
- [ ] `.gitignore` excludes `.env`
- [ ] CORS origins are correct
- [ ] Docker runs as non-root
- [ ] Security scanner passes

### Regular Maintenance
- [ ] Run `pip-audit` weekly
- [ ] Update dependencies monthly
- [ ] Review access logs
- [ ] Test recovery procedures

---

## 5) Threat Model

### Protected Against
- ✅ Path traversal attacks
- ✅ Command injection (allowlist)
- ✅ Malicious dependencies (scanner)
- ✅ Request size attacks (limit)
- ✅ CORS bypass (origin check)

### Not Protected Against
- ❌ Brute force attacks (no rate limiting)
- ❌ API key theft (no auth)
- ❌ Insider threats (no RBAC)
- ❌ Zero-day vulnerabilities

---

## 6) Incident Response

### If Security Alert Triggered
1. **Review alert** from security scanner
2. **Identify affected component**
3. **Rollback if necessary** (requirements.txt auto-rollback)
4. **Document incident**
5. **Update security policies**

### Emergency Contacts
- System administrator
- Security team (if applicable)

---

## 7) Troubleshooting

### Issue 1 — "Security scanner fails"
- **Cause:** Bumblebee or pip-audit not installed
- **Fix:** Install tools or use static scan fallback
- **Prevention:** Include in Docker image

### Issue 2 — "CORS error in browser"
- **Cause:** Origin not in allowed list
- **Fix:** Add origin to `ALLOWED_ORIGINS`
- **Prevention:** Document all access points

### Issue 3 — "Path traversal blocked"
- **Cause:** Attempting to access files outside workspace
- **Fix:** Use valid workspace paths
- **Prevention:** Validate all file operations

---

## 8) Change Log

- 2026-06-15 — Documented actual security features
- 2025-12-24 — Original template created