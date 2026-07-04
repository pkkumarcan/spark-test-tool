---
chapter_id: X99
title: "Appendices"
layer: "Governance"
status: "implemented"
purpose: "Reference sheets, terminal command index, configurations, and directory structure map"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "15m"
inputs:
  - "manual/"
outputs:
  - "None"
qc_gates:
  - "None"
default_tools:
  primary: "markdown"
  fallback: "markdown"
smoke_tests:
  - "None"
hooks:
  validate: "validate_X99"
  run: "run_X99"
  score: "score_X99"
  retry: "retry_X99"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED"
  max_retries: 1
---

# X99 — Appendices

## Chapter Card
**Chapter:** `X99 — Appendices`  
**Layer:** `Governance`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Reference manual containing full pipeline command cheatsheets and workspace folder maps.  
**Last Verified:** 2026-06-17  

---

## 1) Standard Directory Structures

### Workspace Directory Layout
```
/home/pkkumar/AGGY/spark-test-tool/
├── app/
│   ├── backends/              # Backend services and scanner utilities
│   ├── data/                  # Active agent context, RAG sources, and databases
│   └── static/                # Static assets and lead magnets
├── jobs/                      # Pipeline execution outputs (ephemeral/production)
│   └── <job_id>/
│       ├── 01_audio/          # Voiceovers, music stems, mixdowns
│       ├── 02_video/          # keyframes, video clips, renders
│       ├── 03_publish/        # Finished packaging artifacts
│       └── 99_logs/           # Local execution logs and reports per chapter
└── manual/                    # Operations Manual (Chapters X01 - X114)
```

---

## 2) Command Cheatsheet

### Pipeline Smoke Testing
Run system diagnostics and check tool integrations:
```bash
python run_smoke_tests.py
```

### Script Integrity Audits
Validate spelling, ad-suitability, and markup checks:
```bash
python -m unittest tests/test_validation.py
```

### Cleaning Up Temporary Outputs
Clear workspace caches:
```bash
find jobs/ -type d -name "99_logs" -exec rm -rf {} +
```

---

## 3) Environment Variables Reference (`.env`)

| Variable | Default Value | Purpose |
|----------|---------------|---------|
| `ALLOWED_ORIGINS` | `http://localhost:5050` | CORS trusted whitelist domains |
| `DATABASE_PATH` | `/app/data/prod.db` | Path to sqlite runtime database |
| `LLM_PROVIDER` | `ollama` | Generation orchestrator backend |
| `TTS_PROVIDER` | `elevenlabs` | Voice generation backend |

---

## 4) Change Log (Chapter Local)

- 2026-06-17 — Created reference indices and folder maps.
