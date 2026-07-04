---
chapter_id: X13
title: "Master Story Script"
layer: "Planning"
status: "implemented"
purpose: "Generate a structured script outline with narration and visual cues via Ollama"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "30m"
inputs:
  - "topic"
  - "scenes_count"
outputs:
  - "JSON-structured script array"
qc_gates:
  - "Script array contains exactly scenes_count items"
  - "All objects have narration and image_prompt fields"
default_tools:
  primary: "Ollama (qwen3:14b / qwen3:8b)"
  fallback: "None"
hooks:
  validate: "validate_X13"
  run: "run_X13"
---

# X13 — Master Story Script

## Chapter Card
**Chapter:** `X13 — Master Story Script`  
**Layer:** `Planning`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Generate a structured script outline with narration and visual cues via Ollama.  
**Last Verified:** 2026-06-16

**Inputs:**
- `topic` (String)
- `scenes_count` (Integer)

**Outputs:**
- JSON-formatted scene list (staged in memory/cache)

---

## 1) Quickstart (Golden Path)

### Goal
Query Ollama to generate a scene-by-scene script detailing narrations and visual prompts.

### Steps
1. The script generation is triggered automatically as the first step of the Chained Story pipeline:
   ```bash
   curl -X POST http://localhost:5050/api/chain/generate \
     -H "Content-Type: application/json" \
     -d '{"topic": "Artificial Intelligence in 2026", "scenes_count": 3}'
   ```
2. Verify the structured JSON response contains narration and prompt fields for each scene.

---

## 2) Code Reference

- **Source Code:** [chained_generator.py:37–101](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/chained_generator.py#L37-L101)
- **Primary Endpoint:** `/api/chain/generate`
