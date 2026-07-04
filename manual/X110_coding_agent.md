---
chapter_id: X110
title: "Coding Agent"
layer: "Integration"
status: "implemented"
purpose: "Triggers stateful workspace coding iterations with human approval intercepts"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "30m"
inputs:
  - "task"
  - "model"
outputs:
  - "File write updates or command logs"
qc_gates:
  - "Validation checks restrict modifications inside WORKSPACE_ROOT sandbox"
default_tools:
  primary: "Ollama (qwen3:8b) + shlex/subprocess"
  fallback: "None"
---

# X110 — Coding Agent

## Chapter Card
**Chapter:** `X110 — Coding Agent`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Triggers stateful workspace coding iterations with human approval intercepts.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Instruct the coding agent to resolve a developer task.

### Steps
1. Submit a coding agent request:
   ```bash
   curl -X POST http://localhost:5050/api/gems/coding-agent \
     -H "Content-Type: application/json" \
     -d '{"task": "Add a new print statement to scratch/test.py", "model": "qwen3:8b"}'
   ```
2. Verify loop resolution logs and local file output checks.
