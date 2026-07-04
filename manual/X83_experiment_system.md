---
chapter_id: X83
title: "Experiment System"
layer: "Post-Publishing"
status: "implemented"
purpose: "Set up and validate title or thumbnail A/B experiments to maximize click-through rate (CTR)"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "30m"
inputs:
  - "kpi_report.json"
outputs:
  - "ab_test_report.json"
qc_gates:
  - "ctr_gain_detected == True"
default_tools:
  primary: "python/ab_split_tester"
  fallback: "Manual split test spreadsheet"
smoke_tests:
  - "A_minimal"
hooks:
  validate: "validate_X83"
  run: "run_X83"
  score: "score_X83"
  retry: "retry_X83"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED"
  max_retries: 2
---

# X83 — Experiment System

## Chapter Card
**Chapter:** `X83 — Experiment System`  
**Layer:** `Post-Publishing`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Schedule, manage, and calculate winning variations in title or thumbnail A/B split testing.  
**Last Verified:** 2026-06-17  

---

## 1) Procedure (Operator Steps)

### Step 1 — Setup Experiment
- Define Variant A and Variant B (e.g. contrast thumbnail vs face thumbnail).
- Run split testing endpoints to query variants after 48 hours.
- Calculate winning CTR with statistical significance.

---

## 2) Change Log (Chapter Local)

- 2026-06-17 — Wrote A/B testing splits protocol.
