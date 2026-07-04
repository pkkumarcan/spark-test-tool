---
chapter_id: X104
title: "Financial Analyst"
layer: "Integration"
status: "implemented"
purpose: "Retrieve live stock/crypto tickers and compile financial reports"
owner: "Agent"
last_updated: "2026-06-16"
estimated_time: "10m"
inputs:
  - "ticker symbol"
outputs:
  - "JSON/Markdown market analysis"
qc_gates:
  - "Successful ticker lookup response"
default_tools:
  primary: "Ollama + YFinance parsing"
  fallback: "None"
---

# X104 — Financial Analyst

## Chapter Card
**Chapter:** `X104 — Financial Analyst`  
**Layer:** `Integration`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Retrieve live stock/crypto tickers and compile financial reports.  
**Last Verified:** 2026-06-16

---

## 1) Quickstart (Golden Path)

### Goal
Retrieve live financial data and analysis for a given ticker symbol.

### Steps
1. Execute the analysis endpoint:
   ```bash
   curl -X POST http://localhost:5050/api/gems/finance \
     -H "Content-Type: application/json" \
     -d '{"ticker": "NVDA"}'
   ```
2. Verify ticker prices, averages, and trend evaluations in the returned JSON.
