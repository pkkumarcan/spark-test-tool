---
chapter_id: X102
title: "MoA Chat"
layer: "Integration"
status: "implemented"
purpose: "Aggregate responses from multiple local models using a Mixture of Agents structure"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "query prompt"
outputs:
  - "Consolidated synthesis response"
qc_gates:
  - "Successful inference across child agents"
default_tools:
  primary: "Ollama (qwen3:8b, llama3:8b, phi3:3.8b)"
  fallback: "Single model chat"
hooks:
  validate: "validate_X102"
  run: "run_X102"
---

# X102 — MoA Chat

## Chapter Card
**Chapter:** `X102 — MoA Chat`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Aggregate responses from multiple local models using a Mixture of Agents structure.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Query the MoA chatbot and retrieve a multi-agent consolidated answer.

### Steps
1. Execute the POST query:
   ```bash
   curl -X POST http://localhost:5050/api/moa/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Compare PyTorch and TensorFlow in one paragraph."}'
   ```
2. Retrieve the combined response synthesizing output from child LLM workers.
