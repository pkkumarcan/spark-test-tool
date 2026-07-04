---
chapter_id: X32
title: "DAW Templates"
layer: "Audio-Music"
status: "implemented"
purpose: "Configure sidechain compression and routing thresholds for automated mixing"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "speech WAV files"
  - "soundtrack WAV files"
outputs:
  - "combined mixed WAV audio track"
qc_gates:
  - "background track ducking drops by exactly -12dB when speech triggers"
default_tools:
  primary: "FastAPI + FFmpeg filter complex"
  fallback: "None"
---

# X32 — DAW Templates

## Chapter Card
**Chapter:** `X32 — DAW Templates`  
**Layer:** `Audio-Music`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Configure sidechain compression and routing thresholds for automated mixing.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Apply ducking sidechain parameters to narration and background music tracks.

### Steps
1. The mixing template is executed inside the final FFmpeg audio compilation stage:
   - Uses `amix` or `sidechain` dynamic range filters.
   - Reduces background levels when narration voice signals are detected.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:226–236](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L226-L236)
- **Primary Endpoint:** `/api/chain/generate` (internal compile loop)
