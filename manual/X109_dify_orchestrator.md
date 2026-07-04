---
chapter_id: X109
title: "Dify Orchestrator"
layer: "Integration"
status: "implemented"
purpose: "Trigger external Dify workflow applications in streaming or blocking modes"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "workflow_id"
  - "inputs"
outputs:
  - "Dify workflow execution payload results"
qc_gates:
  - "HTTP 200 connection response from Dify platform"
default_tools:
  primary: "FastAPI + httpx + Dify API"
  fallback: "None"
---

# X109 — Dify Orchestrator

## Chapter Card
**Chapter:** `X109 — Dify Orchestrator`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Trigger external Dify workflow applications in streaming or blocking modes.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Trigger a configured Dify workflow and receive execution statistics.

### Steps
1. Execute the trigger workflow endpoint:
   ```bash
   curl -X POST http://localhost:5050/api/dify/run-workflow \
     -H "Content-Type: application/json" \
     -d '{"workflow_id": "test_workflow_123", "inputs": {"query": "Hello Dify"}}'
   ```
2. Verify execution status metrics inside the returned JSON payload.
