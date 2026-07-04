---
chapter_id: X93
title: "Monetization Overview"
layer: "Governance"
status: "implemented"
purpose: "Govern monetization pipelines, ad revenue positioning, digital offers, and ethical commercialization policies"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - "config.monetization_settings"
outputs:
  - "monetization_report.json"
qc_gates:
  - "ad_suitability_score >= 0.85"
default_tools:
  primary: "Ollama/Qwen3-14B"
  fallback: "Manual Review Guide"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X93"
  run: "run_X93"
  score: "score_X93"
  retry: "retry_X93"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X93 — Monetization Overview

## Chapter Card
**Chapter:** `X93 — Monetization Overview`  
**Layer:** `Governance`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Map out offer positioning, ad-suitability compliance, and monetization funnel strategies.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `config.monetization_settings` (pricing tables, target offer URLs)
- `/jobs/<job_id>/job_manifest.json`

**Outputs (files):**
- `/jobs/<job_id>/99_logs/X93/monetization_report.json`

**Quality Gates (must pass):**
- `ad_suitability_score >= 0.85`: Generated narration script must not contain swear words, violence, or controversial topics that trigger YouTube demonetization.

**Default tools:**
- `Ollama/Qwen3-14B` (primary ad-suitability auditor)
- `Manual Review Guide` (fallback auditing process)

**Automation hooks:**
- `validate_X93(job_id)`
- `run_X93(job_id, profile)`
- `score_X93(job_id)`
- `retry_X93(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Audit generated scripts and video metadata to ensure they meet monetization requirements and embed promotional links dynamically.

### When to run this chapter
- Immediately after script writing (Chapter X13).
- Prior to final publication packages draft (Chapter X18).

### Default steps (golden path)
1) Load script text from the job manifest file.
2) Submit the script to Qwen3 using the ad-suitability template to scan for prohibited topics.
3) Inject promotional offer links from `config.monetization_settings` into the video descriptions.
4) Output findings to `monetization_report.json`.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/99_logs/X93/monetization_report.json`
- [ ] QC passed: Ad-suitability rating is green.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X93]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Narration Script | `job_manifest.json -> script` | Script to scan |
| Offers list | `config.monetization_settings.offers` | Active promotional links |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Audit Report | `/jobs/<job_id>/99_logs/X93/monetization_report.json` | Compliance rating report |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Ad-Suitability Rules
- No profanity, violence, or sensitive topics.
- Clear disclosure tags (e.g. `[Sponsored]`, `#ad`) must be placed in descriptions if affiliate links are active.

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Ollama with Qwen3-14B
  - **Version/pin:** Qwen 3 14B JSON Mode
  - **Compute notes:** Runs on GPU (requires 8GB VRAM)
  - **Strengths:** High vocabulary understanding and policy compliance classification.

---

## 5) Procedure (Operator Steps)

### Step 1 — Verify Script Suitability
- **Inputs:** `script` string.
- **Action:** Send to Qwen3 requesting a binary classification:
  ```json
  {
    "system": "You are a YouTube policy auditor. Classify this text as either SAFE or DEMONETIZED.",
    "prompt": "<script text>"
  }
  ```
- **Expected output:** Returns `"SAFE"`.
- **Common failures:** False positives on historical or technical terms (e.g. "exploit", "execution").
- **Fix:** Manually flag as `SAFE` in logs if context is technical.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X93(job_id)`: Checks for script files.
- `run_X93(job_id, profile)`: Dispatches the audit task.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Classify a clean short sentence.
- **Pass criteria:** Returns `"SAFE"`.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] YouTube disclosure label included if affiliate link exists.
- [ ] Language complies with advertiser-friendly guidelines.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `ad_suitability_score`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Demonetization Flag Triggered
- **Cause:** Prompt contained sensitive triggering words.
- **Fix:** Rewrite the paragraph to use softer terms (e.g. replace "kill process" with "terminate process").

---

## 11) Examples (Copy-paste)
- Example python checking snippet:
  ```python
  import json
  report = {"ad_suitability": "SAFE", "disclaimer_included": True}
  print(json.dumps(report))
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X93/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Wrote monetization policy and verification guidelines.
