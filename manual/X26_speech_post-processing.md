---
chapter_id: X26
title: "Speech Post-Processing"
layer: "Audio-Speech"
status: "implemented"
purpose: "Apply compression, dynamic EQ, and normalization to narration audio"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "raw WAV file"
outputs:
  - "normalized processed WAV file"
qc_gates:
  - "output target loudness falls between -16 to -18 LUFS"
default_tools:
  primary: "FFmpeg filters / Pydub"
  fallback: "None"
---

# X26 — Speech Post-Processing

## Chapter Card
**Chapter:** `X26 — Speech Post-Processing`  
**Layer:** `Audio-Speech`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Apply compression, dynamic EQ, and normalization to narration audio.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Apply audio equalization and normalization steps to voice files.

### Steps
1. The post-processing steps execute in the FFmpeg audio compilation stage:
   - Normalizes audio peak levels using `loudnorm` filter parameters.
   - Adjusts vocal equalization bands.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:220–235](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L220-L235)
- **Primary Endpoint:** `/api/chain/generate` (internal compile loop)
