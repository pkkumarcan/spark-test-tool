---
chapter_id: X114
title: "Chat Orchestrator"
layer: "Integration"
status: "implemented"
purpose: "Classify user intent using Gemma4 and route requests to specialized backend targets"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "user query message"
  - "conversation history"
outputs:
  - "routed response or action tab metadata parameters"
qc_gates:
  - "Model intent routing accuracy conforms to standard categories"
default_tools:
  primary: "Ollama (gemma4:12b-it-qat)"
  fallback: "Ollama (llama3)"
---

# X114 — Chat Orchestrator

## Chapter Card
**Chapter:** `X114 — Chat Orchestrator`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Classify user intent using Gemma4 and route requests to specialized backend targets.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Interact with the chatbot to automatically trigger action generation cards.

### Steps
1. Execute the main chat gateway:
   ```bash
   curl -X POST http://localhost:5050/api/orchestrator/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Generate a beautiful video of a sunset over the ocean"}'
   ```
2. Verify that the response includes routed action metadata (`"action": "video"`) alongside the chat reply.
