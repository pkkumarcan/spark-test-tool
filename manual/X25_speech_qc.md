---
chapter_id: X25
title: "Speech QC"
layer: "Audio-Speech"
status: "implemented"
purpose: "Verify vocal clarity, check clipping thresholds, and enforce sample rates"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "generated WAV audio file"
outputs:
  - "clipping and frequency diagnostic reports"
qc_gates:
  - "WAV sample rate is 44100Hz and peaks do not exceed -1dBFS"
default_tools:
  primary: "Python soundfile + numpy"
  fallback: "None"
---

# X25 — Speech QC

## Chapter Card
**Chapter:** `X25 — Speech QC`  
**Layer:** `Audio-Speech`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Verify vocal clarity, check clipping thresholds, and enforce sample rates.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Audit generated voice WAV files for quality parameters before stitching.

### Steps
1. The Voice AI Agent pipeline triggers automated quality checks on output files:
   - Reads WAV file headers.
   - Audits signal peak amplitudes to verify they don't clip at `0dBFS`.

---

## 2) Code Reference

- **Source Code:** [voice_agent.py](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/voice_agent.py)
- **Primary Endpoint:** `/api/gems/voice`
