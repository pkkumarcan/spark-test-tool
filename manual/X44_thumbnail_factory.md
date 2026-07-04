---
chapter_id: X44
title: "Thumbnail Factory"
layer: "Images"
status: "implemented"
purpose: "Crop image frames and overlay styled titles for CTR optimization"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "background visual image"
  - "thumbnail text prompt"
outputs:
  - "final 1280x720 JPG thumbnail asset"
qc_gates:
  - "output resolution matches 1280x720"
default_tools:
  primary: "Pillow (PIL) + FLUX"
  fallback: "None"
---

# X44 — Thumbnail Factory

## Chapter Card
**Chapter:** `X44 — Thumbnail Factory`  
**Layer:** `Images`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Crop image frames and overlay styled titles for CTR optimization.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Overlay big, bold CTR-optimized title text over generated background files.

### Steps
1. The canvas layout generation is run during image generation steps:
   - Scales the source frame.
   - Applies text composite stamps.

---

## 2) Code Reference

- **Source Code:** [comfyui_image.py](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/comfyui_image.py)
- **Primary Endpoint:** `/api/image/generate`
