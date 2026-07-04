---
chapter_id: X15
title: "Visual Script Pack"
layer: "Planning"
status: "implemented"
purpose: "Extract scene image prompts and trigger diffusion generation"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "JSON scene list"
outputs:
  - "staged visual png files per scene"
qc_gates:
  - "image_prompt strings include the designated style modifier"
default_tools:
  primary: "FastAPI + ComfyUI"
  fallback: "None"
---

# X15 — Visual Script Pack

## Chapter Card
**Chapter:** `X15 — Visual Script Pack`  
**Layer:** `Planning`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Extract scene image prompts and trigger diffusion generation.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Extract visual prompts from the script and feed them to the ComfyUI rendering loop.

### Steps
1. The visual prompt mapping is executed inside the Chained Story pipeline:
   - Loops through parsed scenes array.
   - Extracts the `image_prompt` field.
   - Submits the prompt to ComfyUI via `/api/image/generate`.

---

## 2) Code Reference

- **Channel Visual Guidelines:** [app/data/channels_info.md](file:///home/pkkumar/AGGY/spark-test-tool/app/data/channels_info.md)
- **Source Code:** [chained_generator.py:130–217](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L130-L217)
- **Primary Endpoint:** `/api/chain/generate` (internal loop)
