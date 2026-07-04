---
chapter_id: X97
title: "Upgrade Strategy"
layer: "Governance"
status: "implemented"
purpose: "Govern model versioning updates, schema migrations, and model regression testing"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "30m"
inputs:
  - "manual/X05_model_registry.md"
  - "config.model_defaults"
outputs:
  - "upgrade_validation_report.json"
qc_gates:
  - "compatibility_score >= 0.90"
default_tools:
  primary: "model_registry_check"
  fallback: "Manual migration runbook"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X97"
  run: "run_X97"
  score: "score_X97"
  retry: "retry_X97"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X97 — Upgrade Strategy

## Chapter Card
**Chapter:** `X97 — Upgrade Strategy`  
**Layer:** `Governance`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Provide safety guidelines, version validation, and regression tests when upgrading foundation models or third-party APIs.  
**Last Verified:** 2026-06-17  

**Inputs (files/keys):**
- `manual/X05_model_registry.md` (active model mappings)
- `config.model_defaults` (system fallback targets)

**Outputs (files):**
- `/jobs/<job_id>/99_logs/X97/upgrade_validation_report.json`

**Quality Gates (must pass):**
- `compatibility_score >= 0.90`: Validates that a candidate model replacement yields matching response formats (JSON keys, output structure) on benchmark validation payloads.

**Default tools:**
- `model_registry_check` (local validation scripts)
- `Manual migration runbook` (fallback documentation review)

**Automation hooks:**
- `validate_X97(job_id)`
- `run_X97(job_id, profile)`
- `score_X97(job_id)`
- `retry_X97(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-17`  

---

## 1) Quickstart (Golden Path)

### Goal
Safely propose, test, and activate new model releases in the pipeline registry without disrupting active rendering workloads.

### When to run this chapter
- Before changing any foundation model configurations (e.g. swapping Whisper with a new local STT model).
- Upon deprecation notices from upstream APIs (OpenAI, Gemini).

### Default steps (golden path)
1) Propose a new candidate model in the staging config.
2) Run regression tests using predefined prompts to capture output text format.
3) Compare JSON key integrity and schema compatibility.
4) Write evaluation results to `upgrade_validation_report.json`.
5) Commit updates to the Model Registry (Chapter X05) if validation passes.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/99_logs/X97/upgrade_validation_report.json`
- [ ] QC passed: Candidate compatibility index is green.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X97]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Target Model | `config.model_defaults.staging_model` | Model name to evaluate |
| Reference schema | `/app/schemas/` | Standard output format schemas |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Validation Report | `/jobs/<job_id>/99_logs/X97/upgrade_validation_report.json` | Compatability scorecard |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Upgrade Validation Rules
- **No breaking schemas**: Output JSON structure must map perfectly to the active parser code.
- **Rollback availability**: Always keep the previous working version pinned in the registry under `fallback`.

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Local Registry Schema Validator
  - **Version/pin:** Python pydantic / jsonschema
  - **Compute notes:** CPU execution (under 10 seconds).

---

## 5) Procedure (Operator Steps)

### Step 1 — Benchmark Candidate
- **Inputs:** Candidate name and baseline prompts.
- **Action:** Send 3 test prompts, validate output matches expected JSON schemas.
- **Expected output:** Complete valid JSON response.
- **Common failures:** Schema drift or missing fields.
- **Fix:** Update parser adapter script or adjust model system instructions to align format.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X97(job_id)`: Checks staging configurations.
- `run_X97(job_id, profile)`: Runs validation against baseline data.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Verify staging parameters parse without crash.
- **Pass criteria:** Registry verification helper successfully scans active keys.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Fallback configuration targets are verified and online.
- [ ] Pydantic schema validation returns zero warnings.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `compatibility_score`
- `latency_drift_percentage`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Upgraded model output is truncated
- **Cause:** Max token output limit set too low for the new model's density.
- **Fix:** Adjust default max tokens in `config.model_defaults` for the updated model ID.

---

## 11) Change Log (Chapter Local)

- 2026-06-17 — Defined testing protocols for upgrade rollouts and validations.
