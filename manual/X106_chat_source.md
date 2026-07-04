---
chapter_id: X106
title: "Chat with Source"
layer: "Integration"
status: "implemented"
purpose: "Query and retrieve context restricted to a single uploaded source file"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "uploaded file"
  - "message prompt"
outputs:
  - "Source-bounded response"
qc_gates:
  - "Ingest processes and maps source correctly"
default_tools:
  primary: "Ollama + Qdrant payload filters"
  fallback: "None"
---

# X106 — Chat with Source

## Chapter Card
**Chapter:** `X106 — Chat with Source`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Query and retrieve context restricted to a single uploaded source file.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Ask questions bounded specifically to a single target PDF or web page content.

### Steps
1. Ingest a document file via the API:
   ```bash
   curl -X POST http://localhost:5050/api/gems/ingest-source \
     -F "file=@/home/pkkumar/AGGY/spark-test-tool/README.md"
   ```
   *Expected:* Returns a unique `source_id`.
2. Submit a chat query referencing the acquired `source_id`:
   ```bash
   curl -X POST http://localhost:5050/api/gems/chat-source \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the version number of this app?", "source_id": "README.md"}'
   ```
