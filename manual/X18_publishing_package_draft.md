---
chapter_id: X18
title: "Publishing Package Draft"
layer: "Planning"
status: "implemented"
purpose: "Generate video title, tags, and description drafts from narrative contexts"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "15m"
inputs:
  - "JSON scene list"
outputs:
  - "Markdown publishing draft report"
qc_gates:
  - "Metadata includes SEO optimization keywords"
default_tools:
  primary: "Ollama (qwen3:8b)"
  fallback: "None"
---

# X18 — Publishing Package Draft

## Chapter Card
**Chapter:** `X18 — Publishing Package Draft`  
**Layer:** `Planning`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Generate video title, tags, and description drafts from narrative contexts.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Compile optimized publishing title and metadata packages from the script context.

### Steps
1. The metadata compiling is processed inside the Chat Orchestrator intent routing loop:
   - Evaluates the topic prompt.
   - Outputs titles, hashtags, and social descriptions.

---

## 2) Code Reference

- **Source Code:** [orchestrator.py:120–150](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/orchestrator.py#L120-L150)
- **Primary Endpoint:** `/api/orchestrator/chat`
