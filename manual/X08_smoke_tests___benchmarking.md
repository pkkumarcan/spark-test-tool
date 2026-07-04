---
chapter_id: X08
title: "Smoke Tests & Benchmarking"
layer: "Foundation"
status: "implemented"
purpose: "Standard benchmark suite with quality/speed scoring"
owner: "Human/Agent"
last_updated: "2026-06-19"
estimated_time: "1d"
inputs:
  - "target_base_url"
outputs:
  - "smoke_test_report.md"
qc_gates:
  - "run_smoke_tests.py"
default_tools:
  primary: "run_smoke_tests.py"
smoke_tests:
  - "run_tests"
hooks:
  validate: "validate_X08"
  run: "run_X08"
  score: "score_X08"
  retry: "retry_X08"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED"
  max_retries: 3
---

# X08 — Smoke Tests & Benchmarking

## Chapter Card
**Chapter:** `X08 — Smoke Tests & Benchmarking`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Standard benchmark suite with quality/speed scoring  
**Last Verified:** 2026-06-19

---

## 1) Quickstart (Golden Path)

### Goal
Ensure backend APIs are up, models are loaded, and the system performs within expected speed/quality bounds.

### When to run
- After deployment, docker compose restarts, or any core code updates.
- Prior to release.

### Golden Path Steps
1) Ensure the backend server is running locally (default: `http://localhost:5050`).
2) Execute the smoke test script:
   ```bash
   python run_smoke_tests.py
   ```
3) Verify outcomes in [smoke_test_report.md](file:///home/pkkumar/AGGY/spark-test-tool/smoke_test_report.md).

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Target URL | `BASE_URL` | Base URL of the Gateway server (e.g. `http://localhost:5050`) |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Smoke Test Report | `smoke_test_report.md` | Markdown table showing test status (PASS/FAIL) and latency/details for each component |

### Definition of Done (DoD)
- All 16 key endpoints (/health, /api/gpu/status, Ollama, ComfyUI, Whisper, F5-TTS, RAG, MCP, Dify, coding agent, etc.) must respond successfully.
- The `smoke_test_report.md` file is generated with matching results.

---

## 3) Tooling (Approved Stack)

### Primary (default)
- **Tool:** Suite execution script [run_smoke_tests.py](file:///home/pkkumar/AGGY/spark-test-tool/run_smoke_tests.py)

---

## 4) Troubleshooting

### Issue 1 — Test endpoint fails with ConnectionRefused
- **Cause:** Gateway server or target model service is down.
- **Fix:** Start services via docker-compose (`docker compose up -d`) and retry.

---

## 5) Change Log

- 2026-06-19 — Linked existing benchmarking and smoke testing tools, finalized documentation.
