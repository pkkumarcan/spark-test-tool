---
chapter_id: X103
title: "Meme Factory"
layer: "Integration"
status: "implemented"
purpose: "Inject custom captions and generate overlays on meme templates"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "topic"
  - "template"
outputs:
  - "staged meme image"
qc_gates:
  - "ComfyUI generation succeeds"
default_tools:
  primary: "ComfyUI + SDXL/FLUX"
  fallback: "None"
---

# X103 — Meme Factory

## Chapter Card
**Chapter:** `X103 — Meme Factory`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Inject custom captions and generate overlays on meme templates.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Generate a custom overlay meme for a designated topic.

### Steps
1. Call the meme endpoint:
   ```bash
   curl -X POST http://localhost:5050/api/meme/generate \
     -H "Content-Type: application/json" \
     -d '{"topic": "Docker volume permission errors", "template": "distracted_boyfriend"}'
   ```
2. Poll the status using the returned `job_id`.
