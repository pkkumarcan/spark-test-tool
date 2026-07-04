---
chapter_id: X112
title: "Story Chain"
layer: "Integration"
status: "implemented"
purpose: "Chains text, image, audio, and video models to create completed video stories"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "45m"
inputs:
  - "topic"
  - "scenes_count"
outputs:
  - "consolidated story MP4 package"
qc_gates:
  - "Sub-generation pipeline links check out successfully"
default_tools:
  primary: "Ollama + ComfyUI + F5-TTS + FFmpeg"
  fallback: "None"
---

# X112 — Story Chain

## Chapter Card
**Chapter:** `X112 — Story Chain`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Chains text, image, audio, and video models to create completed video stories.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Trigger the chained generator pipeline to output a full story video.

### Steps
1. Execute the chain creation endpoint:
   ```bash
   curl -X POST http://localhost:5050/api/chain/generate \
     -H "Content-Type: application/json" \
     -d '{"topic": "The history of space exploration", "scenes_count": 3}'
   ```
2. Poll statistics using the returned `job_id`.
