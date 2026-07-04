---
chapter_id: X108
title: "Generative UI"
layer: "Integration"
status: "implemented"
purpose: "Synthesize HTML/CSS/JS mockups on the fly from user prompts"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "10m"
inputs:
  - "prompt"
outputs:
  - "HTML/CSS/JS code block"
qc_gates:
  - "HTML output compiles valid layouts"
default_tools:
  primary: "Ollama (qwen3:8b/gemma4)"
  fallback: "None"
---

# X108 — Generative UI

## Chapter Card
**Chapter:** `X108 — Generative UI`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Synthesize HTML/CSS/JS mockups on the fly from user prompts.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Generate a functional frontend widget layout based on a text query.

### Steps
1. Call the Generate UI API:
   ```bash
   curl -X POST http://localhost:5050/api/gems/generate-ui \
     -H "Content-Type: application/json" \
     -d '{"prompt": "A modern dark-mode music player control card with neon gradients"}'
   ```
2. Verify HTML, CSS, and JS components inside the returned structured response.
