---
chapter_id: X85
title: "Community Ops"
layer: "Post-Publishing"
status: "implemented"
purpose: "Parse community comments, evaluate sentiment, and queue canned interaction replies"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "20m"
inputs:
  - "channel_metadata.json"
outputs:
  - "sentiment_report.json"
qc_gates:
  - "sentiment_analysis_complete == True"
default_tools:
  primary: "Ollama/Gemma"
  fallback: "Manual comment check"
smoke_tests:
  - "A_minimal"
hooks:
  validate: "validate_X85"
  run: "run_X85"
  score: "score_X85"
  retry: "retry_X85"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED"
  max_retries: 2
---

# X85 — Community Ops

## Chapter Card
**Chapter:** `X85 — Community Ops`  
**Layer:** `Post-Publishing`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Automate comment retrieval and analyze community audience feedback sentiment.  
**Last Verified:** 2026-06-17  

---

## 1) Change Log (Chapter Local)

- 2026-06-17 — Wrote community ops metrics.
