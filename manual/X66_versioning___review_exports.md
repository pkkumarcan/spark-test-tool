---
chapter_id: X66
title: "Versioning & Review Exports"
layer: "Assembly"
status: "implemented"
purpose: "Track deliverable versioning iterations and manage human/agent review workflow states"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "15m"
inputs:
  - "job_manifest.json"
  - "job_store"
outputs:
  - "review_metadata.json"
qc_gates:
  - "version_tag_format == PASSED"
  - "review_state == APPROVED"
default_tools:
  primary: "Job Store (SQLite/JSON)"
  fallback: "Git tags"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X66"
  run: "run_X66"
  score: "score_X66"
  retry: "retry_X66"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X66 — Versioning & Review Exports

## Chapter Card
**Chapter:** `X66 — Versioning & Review Exports`  
**Layer:** `Assembly`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Record and tag output video versions (v1, v2, v3) in the SQLite database and track user approval logs.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `/jobs/<job_id>/job_manifest.json`
- Database store records (`job_store.py`)

**Outputs (files):**
- `/jobs/<job_id>/99_logs/X66/review_metadata.json`

**Quality Gates (must pass):**
- `version_tag_format == PASSED`: Output version tags must adhere to strict formatting (e.g. `v1.0.0`, `v1.1.0`).
- `review_state == APPROVED`: Deliverable must carry a signed approval key from the user or auditing agent before packaging.

**Default tools:**
- `Job Store (SQLite/JSON)` (primary database state logger)
- `Git tags` (fallback source code version tag manager)

**Automation hooks:**
- `validate_X66(job_id)`
- `run_X66(job_id, profile)`
- `score_X66(job_id)`
- `retry_X66(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Log version history for job deliverables and transition the job status from `COMPLETED` to `APPROVED` based on external user sign-off.

### When to run this chapter
- Immediately after full video assembly and subtitle burn-in.
- Before running the final deliverables bundle packager.

### Default steps (golden path)
1) Read current job information from the SQLite job database.
2) Compute the next version tag increment based on existing entries.
3) Tag the output assets with the computed version suffix (e.g. `final_v1.mp4`).
4) Prompt the user or inspector agent for an approval review signature.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/99_logs/X66/review_metadata.json`
- [ ] QC passed: Database state shows the job is marked `approved`.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X66]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Current Version | `job_store.get_job(job_id).version` | Latest version entry in db |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Review Log | `/jobs/<job_id>/99_logs/X66/review_metadata.json` | Log entry describing review audit trail |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Database States
Jobs must map to one of the following states inside `job_store.py`:
- `PENDING_REVIEW`
- `APPROVED`
- `REJECTED`

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Python Job Store Database (`job_store.py`)
  - **Version/pin:** sqlite3 (Standard Library)
  - **Compute notes:** Runs on CPU (database calls execute in <10ms).

---

## 5) Procedure (Operator Steps)

### Step 1 — Write Review Status
- **Inputs:** `job_id`, approval decision (`approve` or `reject`).
- **Action:**
  - Execute a Python helper script:
    ```python
    import json
    from app.backends import job_store
    
    def approve_deliverable(job_id, user_id):
        # Update SQLite record
        job_store.update_job_status(job_id, "APPROVED")
        # Save local JSON review metadata
        log_path = f"/jobs/{job_id}/99_logs/X66/review_metadata.json"
        with open(log_path, "w") as f:
            json.dump({"approved_by": user_id, "status": "APPROVED"}, f)
    ```
- **Expected output:** Returns positive update confirmation.
- **Common failures:** Database lock error.
- **Fix:** Wait 1 second and retry database write operation.

---

## 6) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Update a mock SQLite entry.
- **Pass criteria:** Return value confirms row change counts.

---

## 7) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Status key in SQLite shows `APPROVED`.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `review_turnaround_seconds`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Version ID Collisions
- **Cause:** Parallel worker pipelines updating the same job row simultaneously.
- **Fix:** Enforce transaction locks on the database file using Python's `sqlite3` context managers.

---

## 11) Change Log (Chapter Local)

- 2026-06-15 — Wrote database-backed versioning and approval logs.
