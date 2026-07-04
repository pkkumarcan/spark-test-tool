---
chapter_id: X20
title: "Production Blueprint Export"
layer: "Planning"
status: "implemented"
purpose: "Export fully compiled assets and scripts to the local directory"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "job_id"
outputs:
  - "output asset file link and JSON metadata"
qc_gates:
  - "File output size is non-zero"
default_tools:
  primary: "FastAPI + job_store.py"
  fallback: "None"
---

# X20 — Production Blueprint Export

## Chapter Card
**Chapter:** `X20 — Production Blueprint Export`  
**Layer:** `Planning`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Export fully compiled assets and scripts to the local directory.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Locate and verify fully compiled production outputs and export data.

### Steps
1. Query completed job status:
   ```bash
   curl http://localhost:5050/api/jobs/story_1234abcd
   ```
2. Verify output URL parameters point to valid compiled media `/output/story_1234abcd.mp4`.

---

## 2) Code Reference

- **Source Code:** [job_store.py:177–187](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/job_store.py#L177-L187)
- **Primary Endpoint:** `/api/jobs/{job_id}`
