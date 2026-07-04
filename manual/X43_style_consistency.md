---
chapter_id: X43
title: "Style Consistency"
layer: "Images"
status: "implemented"
purpose: "Configure character and environment style consistency across generation batches"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "style tag parameters"
outputs:
  - "staged visual frames with consistent style profiles"
qc_gates:
  - "style parameters are injected into prompt strings"
default_tools:
  primary: "ComfyUI IP-Adapter / ControlNet"
  fallback: "None"
---

# X43 — Style Consistency

## Chapter Card
**Chapter:** `X43 — Style Consistency`  
**Layer:** `Images`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Configure character and environment style consistency across generation batches.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Configure constant visual styles (cinematic, animated, realistic) across multi-scene rendering scripts.

### Steps
1. Visual style modifier is applied inside the generation prompt loop:
   - Appends style strings (e.g. `style` body parameter) to image prompts.
   - Prepares and injects constant parameters into ComfyUI KSampler structures.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:42–44](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L42-L44)
- **Primary Endpoint:** `/api/chain/generate` (internal loop)
