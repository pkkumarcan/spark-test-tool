---
chapter_id: X07
title: "Operations Runbook"
layer: "Foundation"
status: "implemented"
purpose: "Daily/weekly maintenance checklists and housekeeping"
owner: "Human/Agent"
last_updated: "2026-06-19"
estimated_time: "1d"
inputs:
  - "max_file_age_days"
  - "max_db_age_days"
outputs:
  - "housekeeping_report"
qc_gates:
  - "check_disk_space"
  - "prune_old_files"
default_tools:
  primary: "housekeeping.py"
smoke_tests:
  - "run_housekeeping"
hooks:
  validate: "validate_X07"
  run: "run_X07"
  score: "score_X07"
  retry: "retry_X07"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED"
  max_retries: 3
---

# X07 — Operations Runbook

## Chapter Card
**Chapter:** `X07 — Operations Runbook`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Daily/weekly maintenance checklists and housekeeping  
**Last Verified:** 2026-06-19

---

## 1) Quickstart (Golden Path)

### Goal
Keep storage clean, prune database tables, check space, and ensure continuous operation.

### When to run
- Daily / Weekly cron jobs.
- Whenever disk usage warnings trigger (>90% utilization).

### Golden Path Steps
1) Run `run_housekeeping(max_file_age_days=7, max_db_age_days=30)` via [housekeeping.py](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/housekeeping.py).
2) Monitor disk space alerts.
3) Keep logs under control.

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| File Max Age | `max_file_age_days` | Number of days to retain output files |
| DB Record Max Age | `max_db_age_days` | Number of days to retain SQLite job logs |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Housekeeping Report | JSON format | Includes files pruned count, db optimization status, disk usage statistics |

### Definition of Done (DoD)
- Orphaned output files older than threshold are successfully deleted.
- SQLite database is vacuumed to reclaim storage space.
- Disk usage statistics are returned correctly.

---

## 3) Tooling (Approved Stack)

### Primary (default)
- **Tool:** Housekeeping module [housekeeping.py](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/housekeeping.py)

---

## 4) Troubleshooting

### Issue 1 — Disk Space warning is high
- **Cause:** Large video files accumulate in `/app/output`.
- **Fix:** Manually execute or reduce the `max_file_age_days` retention to free up space.

---

## 5) Change Log

- 2026-06-19 — Implemented automated housekeeping routines and finalized documentation.
