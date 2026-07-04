---
chapter_id: X14
title: "Voiceover Script Pack"
layer: "Planning"
status: "implemented"
purpose: "Extract narration text blocks and route to speech synthesis"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "JSON scene list"
outputs:
  - "staged WAV speech files per scene"
qc_gates:
  - "narration strings are parsed without markdown syntax"
default_tools:
  primary: "FastAPI + JSON parser"
  fallback: "None"
---

# X14 — Voiceover Script Pack

## Chapter Card
**Chapter:** `X14 — Voiceover Script Pack`  
**Layer:** `Planning`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Extract narration text blocks and route to speech synthesis.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Extract narration strings from the master script and stage them for voice synthesis.

### Steps
1. The narration extraction happens in the Chained Story pipeline:
   - Loops through parsed scenes array.
   - Extracts the `narration` field string value.
   - Routes the narration string directly to `/api/audio/speak`.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:113–129](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L113-L129)
- **Primary Endpoint:** `/api/chain/generate` (internal loop)
