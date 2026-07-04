---
chapter_id: X74
title: "Platform Export Presets"
layer: "Publishing"
status: "implemented"
purpose: "Configure platform resolution specifications, video bitrates, and aspect ratio crop maps"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "15m"
inputs:
  - "job_manifest.json"
outputs:
  - "export_preset_validation.json"
qc_gates:
  - "aspect_ratio_valid == True"
default_tools:
  primary: "ffmpeg/codec_check"
  fallback: "Manual inspect"
smoke_tests:
  - "A_minimal"
hooks:
  validate: "validate_X74"
  run: "run_X74"
  score: "score_X74"
  retry: "retry_X74"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED"
  max_retries: 2
---

# X74 — Platform Export Presets

## Chapter Card
**Chapter:** `X74 — Platform Export Presets`  
**Layer:** `Publishing`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Enforce aspect ratio formatting and audio/video codec compliance.  
**Last Verified:** 2026-06-17  

---

## 1) Export Standards

- **YouTube Standard Video:** 1920x1080 (16:9), H.264 video codec, AAC audio codec, 15+ Mbps bitrate.
- **YouTube Shorts:** 1080x1920 (9:16), H.264 video codec, AAC audio codec.

---

## 2) Change Log (Chapter Local)

- 2026-06-17 — Defined platform export presets.
