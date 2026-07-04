---
chapter_id: X101
title: "Mail Agent"
layer: "Integration"
status: "implemented"
purpose: "Synchronise, filter, and purge junk emails via Yahoo IMAP"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "YAHOO_EMAIL"
  - "YAHOO_APP_PASSWORD"
outputs:
  - "Local DB index of emails"
qc_gates:
  - "IMAP connection successful"
  - "SQLite write operations successful"
default_tools:
  primary: "FastAPI + aiosqlite"
  fallback: "None"
smoke_tests:
  - "A_minimal"
hooks:
  validate: "validate_X101"
  run: "run_X101"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED"
  max_retries: 2
---

# X101 — Mail Agent

## Chapter Card
**Chapter:** `X101 — Mail Agent`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Synchronise, filter, and purge junk emails via Yahoo IMAP.  
**Last Verified:** 2026-06-16

**Inputs:**
- `YAHOO_EMAIL` (env variable)
- `YAHOO_APP_PASSWORD` (env variable)

**Outputs:**
- Sync status and logged operations
- Local SQLite database `emails.db`

---

## 1) Quickstart (Golden Path)

### Goal
Synchronise email headers from the remote Yahoo server and preview cleanup stats.

### Steps
1. Verify `YAHOO_EMAIL` and `YAHOO_APP_PASSWORD` are configured in `.env`.
2. Start the synchronization task:
   ```bash
   curl -X POST http://localhost:5050/api/mail/sync/start -H "Content-Type: application/json" -d '{"folder": "INBOX", "segment": "all"}'
   ```
3. Poll statistics to check progress:
   ```bash
   curl http://localhost:5050/api/mail/stats
   ```
4. Preview the staged cleanup list:
   ```bash
   curl http://localhost:5050/api/mail/cleanup/preview
   ```

---

## 2) Config & Code Reference

- **Developer API Specifications:** [docs/MAIL_AGENT.md](file:///home/pkkumar/AGGY/spark-test-tool/docs/MAIL_AGENT.md)
- **Source File:** [mail_routes.py](file:///home/pkkumar/AGGY/spark-test-tool/app/mail_agent/mail_routes.py)
- **Primary Endpoint:** `/api/mail/sync/start`
- **Database Path:** Local SQLite DB file under `app/mail_agent/` configuration mappings.
