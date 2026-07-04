---
chapter_id: X107
title: "Voice Agent"
layer: "Integration"
status: "implemented"
purpose: "Converts audio recordings to voice agent replies using Whisper and F5-TTS"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "audio voice WAV file"
outputs:
  - "synthesized agent WAV response file"
qc_gates:
  - "Whisper transcription and F5-TTS speak synthesis both pass"
default_tools:
  primary: "Whisper + Ollama + F5-TTS"
  fallback: "None"
---

# X107 — Voice Agent

## Chapter Card
**Chapter:** `X107 — Voice Agent`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Converts audio recordings to voice agent replies using Whisper and F5-TTS.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Interact with the voice assistant via audio files.

### Steps
1. Call the voice agent endpoint with an input recording:
   ```bash
   curl -X POST http://localhost:5050/api/gems/voice \
     -F "file=@/home/pkkumar/AGGY/spark-test-tool/scratch/input_speech.wav"
   ```
2. Verify that the response is a binary WAV file containing synthesized audio of the agent's reply.
