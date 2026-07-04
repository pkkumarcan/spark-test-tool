---
chapter_id: X17
title: "Edit Blueprint (EDL-lite)"
layer: "Planning"
status: "implemented"
purpose: "Generate dynamic text lists mapping clip timelines and audio parameters"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "JSON scene list"
outputs:
  - "FFmpeg concat file configuration"
qc_gates:
  - "Path formatting resolves correctly on the container OS filesystem"
default_tools:
  primary: "FastAPI + Python text writer"
  fallback: "None"
---

# X17 — Edit Blueprint (EDL-lite)

## Chapter Card
**Chapter:** `X17 — Edit Blueprint (EDL-lite)`  
**Layer:** `Planning`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Generate dynamic text lists mapping clip timelines and audio parameters.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Format and output an edit decision list (EDL-lite) concat text file for FFmpeg processing.

### Steps
1. The blueprint creation is executed in the final video compilation step of the Chained Story pipeline:
   - Formulates a `concat.txt` containing references to generated scene MP4 files.
   - Executes FFmpeg using the structured text file to combine clips dynamically.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:241–257](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L241-L257)
- **Primary Endpoint:** `/api/chain/generate` (internal loop)
