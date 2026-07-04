---
chapter_id: X36
title: "Mastering Standards"
layer: "Audio-Music"
status: "implemented"
purpose: "Normalize and limit audio tracks to conform to YouTube/social media loudness rules"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "mixed audio file"
outputs:
  - "mastered final audio output"
qc_gates:
  - "final integrated loudness is -14 LUFS (+/- 1 LUFS)"
  - "maximum true peak limit is -1 dBTP"
default_tools:
  primary: "FFmpeg loudnorm filter"
  fallback: "None"
---

# X36 — Mastering Standards

## Chapter Card
**Chapter:** `X36 — Mastering Standards`  
**Layer:** `Audio-Music`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Normalize and limit audio tracks to conform to YouTube/social media loudness rules.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Audit and master compiled video output tracks to conform to LUFS loudness rules.

### Steps
1. The mastering limits are enforced during final FFmpeg video generation:
   - Uses the `-af loudnorm=I=-14:TP=-1:LRA=11` audio filter string.
   - Limits true peaks to `-1 dBTP` and sets target integrated loudness to `-14 LUFS`.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:228–236](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L228-L236)
- **Primary Endpoint:** `/api/chain/generate` (internal loop)
