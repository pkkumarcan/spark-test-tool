---
chapter_id: X23
title: "Voice Cloning Profiles"
layer: "Audio-Speech"
status: "implemented"
purpose: "Configure zero-shot reference speakers for F5-TTS/Kokoro vocal cloning"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "reference speaker audio WAV file (5-15s)"
  - "reference transcript text"
outputs:
  - "vocal cloning profile config mapping"
qc_gates:
  - "reference wav sample rate is 44100Hz"
default_tools:
  primary: "F5-TTS Reference Speaker / CosyVoice"
  fallback: "None"
---

# X23 — Voice Cloning Profiles

## Chapter Card
**Chapter:** `X23 — Voice Cloning Profiles`  
**Layer:** `Audio-Speech`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Configure zero-shot reference speakers for F5-TTS/Kokoro vocal cloning.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Configure a reference audio speaker mapping to synthesize custom voice models.

### Steps
1. Place the reference voice wav (e.g., `speaker_ref.wav`) inside the voice assets directory.
2. In your `/api/audio/speak` request payload, supply the reference audio path:
   ```json
   {
     "text": "This is synthesized in the cloned voice.",
     "voice": "speaker_ref.wav"
   }
   ```
3. Synthesize the WAV output and verify voice similarity characteristics.

---

## 2) Code Reference

- **Source Code:** [f5_tts.py](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/f5_tts.py)
- **Primary Endpoint:** `/api/audio/speak`
