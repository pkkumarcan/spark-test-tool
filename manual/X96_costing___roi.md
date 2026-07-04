---
chapter_id: X96
title: "Costing & ROI"
layer: "Governance"
status: "implemented"
purpose: "Govern token auditing, API resource costing, runtime billing, and ROI analysis"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "30m"
inputs:
  - "job_manifest.json"
  - "config.cost_limits"
outputs:
  - "cost_audit.json"
qc_gates:
  - "total_cost_usd <= max_allowed_cost"
default_tools:
  primary: "python/cost_calculator"
  fallback: "Manual costing spreadsheet"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X96"
  run: "run_X96"
  score: "score_X96"
  retry: "retry_X96"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X96 — Costing & ROI

## Chapter Card
**Chapter:** `X96 — Costing & ROI`  
**Layer:** `Governance`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Audit pipeline token and API resource costs to calculate exact job expenditures and campaign ROI.  
**Last Verified:** 2026-06-17  

**Inputs (files/keys):**
- `/jobs/<job_id>/job_manifest.json` (usage metrics, execution times)
- `config.cost_limits` (maximum budget cap per run)

**Outputs (files):**
- `/jobs/<job_id>/99_logs/X96/cost_audit.json`

**Quality Gates (must pass):**
- `total_cost_usd <= max_allowed_cost`: Checks that the total accrued API charges (from LLM text generation, speech synthesis, image/video generation) do not cross the limit defined in `config.cost_limits`.

**Default tools:**
- `python/cost_calculator` (custom aggregator script)
- `Manual costing spreadsheet` (fallback auditing process)

**Automation hooks:**
- `validate_X96(job_id)`
- `run_X96(job_id, profile)`
- `score_X96(job_id)`
- `retry_X96(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-17`  

---

## 1) Quickstart (Golden Path)

### Goal
Assess the exact infrastructure and service provider cost incurred by a specific video production job and compare it against projected campaign return.

### When to run this chapter
- Immediately after all assets are created and finalized.
- Part of the final release cycle (Chapter X75).

### Default steps (golden path)
1) Extract raw token counts and generation tallies from the job manifest file.
2) Load price indexes for AI providers (Gemini, ElevenLabs, ComfyUI/Runway).
3) Compute total charges and append to `cost_audit.json`.
4) Evaluate ROI using lead value averages from the attribution report.
5) Assert that costs did not exceed maximum thresholds.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/99_logs/X96/cost_audit.json`
- [ ] QC passed: Total cost is within budget bounds.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X96]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Token Usage | `job_manifest.json -> usage` | Token counts per API |
| Audio/Video count | `job_manifest.json -> assets` | Total durations and frames |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Cost Audit Report | `/jobs/<job_id>/99_logs/X96/cost_audit.json` | JSON format cost ledger |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Global Cost Reference Limits (Sample)
```json
{
  "max_allowed_cost": 5.00,
  "pricing": {
    "llm_per_1k_input": 0.00015,
    "llm_per_1k_output": 0.0006,
    "tts_per_character": 0.00015,
    "video_per_second": 0.05
  }
}
```

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Python Cost Aggregator
  - **Version/pin:** Python 3.10+
  - **Compute notes:** Runs instantly on CPU.

---

## 5) Procedure (Operator Steps)

### Step 1 — Compile Cost Metrics
- **Inputs:** Raw usage logs.
- **Action:** Execute parsing function to sum all variables.
- **Expected output:** Aggregate dollar values.
- **Common failures:** Missing usage objects in intermediate pipeline step logs.
- **Fix:** Provide conservative defaults when exact counts are missing.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X96(job_id)`: Verifies all upstream usage metadata is present.
- `run_X96(job_id, profile)`: Evaluates cost metrics against thresholds.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Verify calculator runs without crashing on dummy manifest entries.
- **Pass criteria:** Returns cost and sets status to PASSED.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] All API resource variables counted.
- [ ] Total cost does not exceed budget.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `total_cost_usd`
- `roi_percentage`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Cost limit exceeded
- **Cause:** Video generator requested excessive frames or LLM had long context loops.
- **Fix:** Tighten limits on max frame generation and token window settings.

---

## 11) Examples (Copy-paste)
- Python Cost Accumulator Snippet:
  ```python
  def calculate_run_cost(manifest_data, pricing):
      total = 0.0
      # Text API
      total += (manifest_data.get("prompt_tokens", 0) / 1000) * pricing["llm_per_1k_input"]
      # TTS API
      total += manifest_data.get("tts_characters", 0) * pricing["tts_per_character"]
      return round(total, 4)
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X96/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-17 — Wrote costing standard and ROI validation formulas.
