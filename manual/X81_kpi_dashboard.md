---
chapter_id: X81
title: "KPI Dashboard"
layer: "Post-Publishing"
status: "implemented"
purpose: "Aggregate channel traffic performance, view count metrics, and average click-through rate (CTR)"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "20m"
inputs:
  - "channel_metadata.json"
outputs:
  - "kpi_report.json"
qc_gates:
  - "api_response_valid == True"
default_tools:
  primary: "youtube-data-analytics-api"
  fallback: "Manual metrics dashboard copy"
smoke_tests:
  - "A_minimal"
hooks:
  validate: "validate_X81"
  run: "run_X81"
  score: "score_X81"
  retry: "retry_X81"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED"
  max_retries: 2
---

# X81 — KPI Dashboard

## Chapter Card
**Chapter:** `X81 — KPI Dashboard`  
**Layer:** `Post-Publishing`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Monitor traffic, view count trends, and CTR metrics.  
**Last Verified:** 2026-06-17  

**Inputs (files/keys):**
- `/jobs/channel_metadata.json`

**Outputs (files):**
- `/jobs/kpi_report.json`

---

## 1) Quickstart (Golden Path)

### Goal
Fetch view counts, watch hours, and click-through rates from the analytics endpoint to generate performance scoring reports.

### When to run this chapter
- Daily or weekly to update active campaigns.

### Default steps (golden path)
1) Dispatch API request to the analytics engine.
2) Calculate aggregate gains.
3) Write outputs to `kpi_report.json`.

---

## 2) Change Log (Chapter Local)

- 2026-06-17 — Wrote analytics dashboard standards.
