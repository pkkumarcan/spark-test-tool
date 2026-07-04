---
chapter_id: X73
title: "Scheduling & Calendar"
layer: "Publishing"
status: "implemented"
purpose: "Schedule publishing releases, track calendar queues, and handle automated cron tasks"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "15m"
inputs:
  - "publish_package.json"
outputs:
  - "schedule_manifest.json"
qc_gates:
  - "publish_time_in_future == True"
default_tools:
  primary: "cron/python-apscheduler"
  fallback: "Google Calendar spreadsheet integration"
smoke_tests:
  - "A_minimal"
hooks:
  validate: "validate_X73"
  run: "run_X73"
  score: "score_X73"
  retry: "retry_X73"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X73 — Scheduling & Calendar

## Chapter Card
**Chapter:** `X73 — Scheduling & Calendar`  
**Layer:** `Publishing`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Schedule uploads and manage future video release events.  
**Last Verified:** 2026-06-17  

**Inputs (files/keys):**
- `/jobs/<job_id>/publish/publish_package.json`

**Outputs (files):**
- `/jobs/schedule_manifest.json` (running list of future posts)

**Quality Gates (must pass):**
- `publish_time_in_future == True`: Ensures that scheduled dates are set in the future.

---

## 1) Quickstart (Golden Path)

### Goal
Assign a future timestamp to a publishing package to queue it for automatic release.

### When to run this chapter
- Immediately after generating the upload package.

### Default steps (golden path)
1) Load the publish package details.
2) Prompt the operator or scheduler logic for release date/time.
3) Record metadata and queue status to `schedule_manifest.json`.

---

## 2) Change Log (Chapter Local)

- 2026-06-17 — Wrote calendar queueing parameters.
