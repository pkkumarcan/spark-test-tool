---
chapter_id: X34
title: "Arrangement for Video"
layer: "Audio-Music"
status: "implemented"
purpose: "Adapt background soundtrack loop durations to match visual timeline blueprints"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "video EDL blueprint"
  - "music loops"
outputs:
  - "arranged music track matching video length"
qc_gates:
  - "audio track duration exactly matches video track duration"
default_tools:
  primary: "FastAPI + FFmpeg loops"
  fallback: "None"
---

# X34 — Arrangement for Video

## Chapter Card
**Chapter:** `X34 — Arrangement for Video`  
**Layer:** `Audio-Music`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Adapt background soundtrack loop durations to match visual timeline blueprints.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Enforce exact duration matching between the soundtrack and video timeline clips.

### Steps
1. The arrangement happens during the compilation step of the Chained Story pipeline:
   - Evaluates the narration track length.
   - Adjusts the background music loop duration via the `-shortest` FFmpeg filter parameter.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:228–236](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L228-L236)
- **Primary Endpoint:** `/api/chain/generate` (internal loop)
