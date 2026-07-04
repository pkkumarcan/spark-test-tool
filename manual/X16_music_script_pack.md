---
chapter_id: X16
title: "Music Script Pack"
layer: "Planning"
status: "implemented"
purpose: "Inject background soundtrack parameters into compilation steps"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "JSON scene list"
outputs:
  - "audio track overlay configurations"
qc_gates:
  - "audio mixing amplitude balance checks pass"
default_tools:
  primary: "FastAPI + FFmpeg"
  fallback: "None"
---

# X16 — Music Script Pack

## Chapter Card
**Chapter:** `X16 — Music Script Pack`  
**Layer:** `Planning`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Inject background soundtrack parameters into compilation steps.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Define and mix background soundtrack files alongside narration audio tracks.

### Steps
1. The background music config is processed during the final compilation step of the Chained Story pipeline:
   - Sets volume ducking levels.
   - Mixes soundtrack wave inputs via FFmpeg overlay filters.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:218–258](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L218-L258)
- **Primary Endpoint:** `/api/chain/generate` (internal loop)
