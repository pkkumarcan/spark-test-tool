---
chapter_id: X33
title: "AI Music Generation"
layer: "Audio-Music"
status: "implemented"
purpose: "Generate music tracks using AI models via ComfyUI"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "prompt"
  - "model"
  - "lyrics"
outputs:
  - "music track WAV/MP3 file"
qc_gates:
  - "audio output is non-zero in size and duration matches configuration"
default_tools:
  primary: "ComfyUI + ACE-Step 1.5 Base"
  fallback: "None"
---

# X33 — AI Music Generation

## Chapter Card
**Chapter:** `X33 — AI Music Generation`  
**Layer:** `Audio-Music`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Generate music tracks using AI models via ComfyUI.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Query ComfyUI to synthesize a background music track based on a text prompt.

### Steps
1. Call the music generation endpoint:
   ```bash
   curl -X POST http://localhost:5050/api/music/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Synthwave background track, 110 BPM", "model": "ace-step-1.5-base"}'
   ```
2. Poll the status using the returned `job_id` via `/api/jobs/{job_id}` until completed.

---

## 2) Code Reference

- **Source Code:** [comfyui_music.py](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/comfyui_music.py)
- **Primary Endpoint:** `/api/music/generate`