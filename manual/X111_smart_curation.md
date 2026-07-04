---
chapter_id: X111
title: "Smart Curation"
layer: "Integration"
status: "implemented"
purpose: "Analyze directory of source videos and generate compilation cuts using face detection"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "30m"
inputs:
  - "source_dir"
  - "strictness"
  - "pacing"
outputs:
  - "compiled MP4 video"
qc_gates:
  - "FFmpeg output renders successfully"
default_tools:
  primary: "Python OpenCV Face Heuristics + FFmpeg"
  fallback: "None"
---

# X111 — Smart Curation

## Chapter Card
**Chapter:** `X111 — Smart Curation`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Analyze directory of source videos and generate compilation cuts using face detection.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Synthesize a video compilation highlights package from raw source recordings.

### Steps
1. Call the curate endpoint:
   ```bash
   curl -X POST http://localhost:5050/api/curate/generate \
     -H "Content-Type: application/json" \
     -d '{"source_dir": "/app/media_ingest", "strictness": 50, "pacing": 3.0}'
   ```
2. Poll statistics using the returned `job_id`.
