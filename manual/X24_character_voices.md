---
chapter_id: X24
title: "Character Voices"
layer: "Audio-Speech"
status: "implemented"
purpose: "Configure gender, age, and style modifiers across speech generation"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "voice gender/age descriptors"
outputs:
  - "cloned character voice models"
qc_gates:
  - "output pitch and formant scales match the character type"
default_tools:
  primary: "Kokoro-v1 Character Models"
  fallback: "None"
---

# X24 — Character Voices

## Chapter Card
**Chapter:** `X24 — Character Voices`  
**Layer:** `Audio-Speech`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Configure gender, age, and style modifiers across speech generation.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Apply specific gender/age voice characteristics to synthesized narration tracks.

### Steps
1. Select from standard preset voice profiles (e.g. `af_bella`, `am_adam` in Kokoro-v1).
2. Trigger the speak API with the character identifier:
   ```bash
   curl -X POST http://localhost:5050/api/audio/speak \
     -H "Content-Type: application/json" \
     -d '{"text": "Hello, I am speaking in a custom character voice.", "voice": "af_bella"}'
   ```
