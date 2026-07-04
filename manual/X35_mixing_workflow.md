---
chapter_id: X35
title: "Mixing Workflow"
layer: "Audio-Music"
status: "implemented"
purpose: "Set target decibel level ratios between voiceover, soundtrack, and sound effects"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "voiceover track"
  - "background track"
outputs:
  - "mixed output audio file"
qc_gates:
  - "dialogue tracks are clearly audible and dynamic peaks do not clip"
default_tools:
  primary: "FastAPI + FFmpeg filter complex"
  fallback: "None"
---

# X35 — Mixing Workflow

## Chapter Card
**Chapter:** `X35 — Mixing Workflow`  
**Layer:** `Audio-Music`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Set target decibel level ratios between voiceover, soundtrack, and sound effects.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Execute an automated volume mix ensuring narration is louder than the soundtrack.

### Steps
1. The mixing levels are configured in the FFmpeg audio compilation parameters:
   - Voiceover is mixed at `volume=1.0` (primary).
   - Background music is mixed at `volume=0.15` (secondary background).
   - Combines the signals using `amix=inputs=2:duration=first`.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:228–236](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L228-L236)
- **Primary Endpoint:** `/api/chain/generate` (internal loop)
