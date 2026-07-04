---
chapter_id: X##
title: "<Title>"
layer: "<Foundation | Planning | Audio-Speech | Audio-Music | Images | Video | Assembly | Publishing | Post | Governance | Integration>"
status: "<implemented | partial | planned | reserved>"
purpose: "<One-line outcome>"
owner: "<Human/Agent>"
last_updated: "<YYYY-MM-DD>"
estimated_time: "<5m | 15m | 30m | 2h | 1d>"
inputs:
  - "<path or manifest key>"
outputs:
  - "<path>"
qc_gates:
  - "<gate + threshold>"
default_tools:
  primary: "<tool/model>"
  fallback: "<tool/model>"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X##"
  run: "run_X##"
  score: "score_X##"
  retry: "retry_X##"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X## — <Title>

## Chapter Card
**Chapter:** `X## — <Title>`  
**Layer:** `<Layer>`  
**Status:** `<Status>`  
**Purpose (1 line):** `<What this chapter produces/achieves>`  
**Last Verified:** `<YYYY-MM-DD>`

**Inputs (files/keys):**
- `<path or manifest key>`

**Outputs (files):**
- `<path>`

**Quality Gates (must pass):**
- `<Gate 1 (threshold)>`
- `<Gate 2 (threshold)>`

**Default tools:**
- `<tool/model> (primary)`
- `<tool/model> (fallback)`

**Automation hooks:**
- `validate_X##(job_id)`
- `run_X##(job_id, profile)`
- `score_X##(job_id)`
- `retry_X##(job_id, strategy)`

**Smoke test time:** `~<5/15/30> min`  
**Owner:** `<Human/Agent>`  
**Last updated:** `<YYYY-MM-DD>`

---

## 1) Quickstart (Golden Path)

### Goal
`<One sentence goal>`

### When to run this chapter
- `<Trigger 1>`
- `<Trigger 2>`

### Default steps (golden path)
1) `<Step 1>`
2) `<Step 2>`
3) `<Step 3>`

### Done looks like
- [ ] Output exists: `<path>`
- [ ] QC passed: `<report or threshold>`
- [ ] Logs saved: `/jobs/<job_id>/99_logs/X##/`
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X##]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| `<Input A>` | `<path or manifest key>` | `<notes>` |

### Optional Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| `<Optional A>` | `<path or key>` | `<notes>` |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| `<Output A>` | `<path>` | `<notes>` |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.<key>` | `<value>` | `<meaning>` |

### Naming conventions (chapter-specific)
- `<rule>`

### Where logs go
- `/jobs/<job_id>/99_logs/X##/`

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** `<name>`
  - **Version/pin:** `<...>`
  - **Compute notes:** `<VRAM/RAM>`
  - **Strengths:** `<...>`
  - **Weaknesses:** `<...>`

### Alternatives (approved)
- `<alternative>` — `<when to use>`

### Avoid / Deprecated
- `<tool>` — `<why>`

---

## 5) Procedure (Operator Steps)

### Step 1 — `<name>`
- **Inputs:** `<...>`
- **Action:** `<...>`
- **Expected output:** `<...>`
- **Common failures:** `<...>`
- **Fix:** `<...>`

### Step 2 — `<name>`
- **Inputs:** `<...>`
- **Action:** `<...>`
- **Expected output:** `<...>`
- **Common failures:** `<...>`
- **Fix:** `<...>`

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X##(job_id) -> {pass: bool, reasons:[], warnings:[]}`
- `run_X##(job_id, profile) -> {status, outputs[], timings, tool_versions}`
- `score_X##(job_id) -> {quality:1-10, speed:1-10, stability:1-10, notes}`
- `retry_X##(job_id, strategy) -> {attempts, best_run_id, comparison_notes}`

### Status machine
- `NOT_STARTED → RUNNING → PASSED`
- `NOT_STARTED → RUNNING → FAILED → RETRIED → PASSED`
- `FAILED → ESCALATE (human)`

### Retry policy (chapter-specific)
- **Max retries:** `3`
- **Allowed variations:** `<prompt/seed/settings/etc>`
- **Escalate if:** `hardware errors | repeated corruption | IP/compliance risk`

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** `prove it works`
- **Input:** `<tiny sample>`
- **Steps:** `<...>`
- **Pass criteria:** `<...>`
- **If fails:** `<top 2 likely fixes>`

### Smoke Test B — Standard (realistic)
- **Goal:** `prove it works on real settings`
- **Input:** `<standard sample>`
- **Steps:** `<...>`
- **Pass criteria:** `<...>`
- **If fails:** `<fallback path>`

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] `<check 1>`
- [ ] `<check 2>`
- [ ] `<check 3>`

### Scoring rubric (1–10)
- **Quality:** `<definition>`
- **Speed:** `<definition>`
- **Stability:** `<definition>`
- **Repeatability:** `<definition>`

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `runtime_seconds`
- `gpu_vram_peak`
- `cpu_peak`
- `disk_io`
- `artifact_size`
- `qc_score`
- `failure_reason`
- `tool_versions`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — `<symptom>`
- **Cause:** `<...>`
- **Fix:** `<...>`
- **Prevention:** `<...>`

(repeat 5–10)

---

## 11) Examples (Copy-paste)
- Example config snippet:
  - `<...>`
- Example manifest snippet:
  - `<...>`
- Example output folder tree:
  - `<...>`

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Artifacts** in `/jobs/<job_id>/...`
2. **Logs** in `/jobs/<job_id>/99_logs/X##/`
3. **Manifest step entry** in `job_manifest.json`:
   - `pipeline_steps[X##] = {status, quality_score, speed_score, stability_score, notes, tool_versions, timings, outputs}`

---

## 13) Change Log (Chapter Local)

- `<YYYY-MM-DD>` — `<what changed + why>`