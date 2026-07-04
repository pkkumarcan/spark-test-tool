---
chapter_id: X45
title: "Keyframes & Storyboard Images"
layer: "Images"
status: "implemented"
purpose: "Generate visual scene keyframes matching narrative timeline frames"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "JSON scene list"
outputs:
  - "staged visual keyframe images"
qc_gates:
  - "images compile successfully and match scene resolutions"
default_tools:
  primary: "ComfyUI + FLUX Schnell"
  fallback: "None"
---

# X45 — Keyframes & Storyboard Images

## Chapter Card
**Chapter:** `X45 — Keyframes & Storyboard Images`  
**Layer:** `Images`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Generate visual scene keyframes matching narrative timeline frames.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Render visual keyframe storyboard sequences from text prompts.

### Steps
1. The keyframe generation runs automatically inside the story chain loop:
   - Evaluates scene prompts.
   - Saves output images to local temporary folders.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:159–216](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L159-L216)
- **Primary Endpoint:** `/api/chain/generate` (internal loop)
