---
chapter_id: X98
title: "Incident Response"
layer: "Governance"
status: "implemented"
purpose: "Govern disaster recovery, service outages, backups, and database restoration procedures"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "30m"
inputs:
  - "config.backup_settings"
outputs:
  - "incident_log.json"
qc_gates:
  - "backup_integrity_checked == True"
default_tools:
  primary: "tar/sqlite3/pg_dump"
  fallback: "Manual notification system"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X98"
  run: "run_X98"
  score: "score_X98"
  retry: "retry_X98"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X98 — Incident Response

## Chapter Card
**Chapter:** `X98 — Incident Response`  
**Layer:** `Governance`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Provide concrete disaster recovery playbooks, database restoration commands, and fallback routines for external service outages.  
**Last Verified:** 2026-06-17  

**Inputs (files/keys):**
- `config.backup_settings` (retention limits, target volumes)

**Outputs (files):**
- `/jobs/incident_log.json` (running incident tracking log)

**Quality Gates (must pass):**
- `backup_integrity_checked == True`: Assures that simulated database restores from latest backups complete with zero errors.

**Default tools:**
- `tar/sqlite3/pg_dump` (backup and recovery binaries)
- `Manual notification system` (fallback operator communications)

**Automation hooks:**
- `validate_X98(job_id)`
- `run_X98(job_id, profile)`
- `score_X98(job_id)`
- `retry_X98(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-17`  

---

## 1) Quickstart (Golden Path)

### Goal
Handle critical service interruptions or database corruption incidents systematically using standard rollback and repair commands.

### When to run this chapter
- Immediately upon pipeline infrastructure crashes or data corruption alerts.
- During monthly routine database backup validations.

### Default steps (golden path)
1) Check service status endpoints to identify if the failure is network-related, provider-related, or local database corruption.
2) For database recovery, verify the timestamp of the latest backup archive.
3) Execute standard restoration scripts to stand up a clean database instance.
4) Run verification queries to check structural integrity.
5) Log the event to `/jobs/incident_log.json`.

### Done looks like
- [ ] Output exists: Database fully functional / Service fallback active.
- [ ] Incident recorded in: `/jobs/incident_log.json`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Backup File | `/backups/latest.sql.gz` | Latest snapshot file |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Restored DB | `/app/data/prod.db` | Working SQLite/Postgres target |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Recovery Reference Commands

### SQLite Database Repair & Restoration
If the local SQLite database becomes corrupted:
```bash
# Export schema and data to SQL dump file
sqlite3 /app/data/prod.db ".recover" > /app/data/recovery.sql

# Restore SQLite database from SQL dump file
sqlite3 /app/data/prod.db.new < /app/data/recovery.sql
mv /app/data/prod.db.new /app/data/prod.db
```

### PostgreSQL Restoration (if active)
```bash
# Restore schema and records
gunzip -c /backups/latest.sql.gz | psql -h localhost -U spark -d spark_factory
```

### Local Jobs Backup
Archive output packages:
```bash
tar -czf /backups/jobs_backup_$(date +%F).tar.gz /jobs/
```

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** `tar / gzip / sqlite3`
  - **Version/pin:** System native
  - **Compute notes:** Fast CPU operations.

---

## 5) Procedure (Operator Steps)

### Step 1 — External API Failure Fallback
- **Inputs:** HTTP 429/500 code from primary audio/video API (e.g. ElevenLabs).
- **Action:** Toggle configuration to activate local fallback models (e.g., local TTS using F5-TTS).
- **Expected output:** Pipeline resumes with fallback assets.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X98(job_id)`: Scans database for locked handles.
- `run_X98(job_id, profile)`: Dispatches backup routine.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Verify that backup directory exists and is writable.
- **Pass criteria:** Test folder write check succeeds.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Active locks on the database are released.
- [ ] Restoration script runs to completion without exit errors.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `recovery_time_objective_seconds`
- `backup_size_bytes`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Disk Full during backup tar extraction
- **Cause:** Archiving job directory without excluding intermediate raw frame caches.
- **Fix:** Run archive excluding ComfyUI intermediate outputs:
  ```bash
  tar --exclude='*/99_logs/*' -czf /backups/jobs_backup.tar.gz /jobs/
  ```

---

## 11) Change Log (Chapter Local)

- 2026-06-17 — Wrote SQLite restoration sequences and fallback mappings.
