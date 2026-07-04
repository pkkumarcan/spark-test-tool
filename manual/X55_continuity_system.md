---
chapter_id: X55
title: "Continuity System"
layer: "Video"
status: "implemented"
purpose: "Maintain consistency of characters, styles, props, and seeds across video production segments"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - "config.style_settings"
  - "job_manifest.json"
outputs:
  - "continuity_report.json"
qc_gates:
  - "seed_variance == FIXED"
  - "style_match_threshold >= 0.80"
default_tools:
  primary: "Ollama/Qwen3-14B"
  fallback: "Python/Random"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X55"
  run: "run_X55"
  score: "score_X55"
  retry: "retry_X55"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X55 — Continuity System

## Chapter Card
**Chapter:** `X55 — Continuity System`  
**Layer:** `Video`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Enforce strict visual and character consistency across multiple sequential generation segments.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `config.style_settings`
- `job_manifest.json` (specifically the character descriptions and prompt templates)

**Outputs (files):**
- `/jobs/<job_id>/99_logs/X55/continuity_report.json`

**Quality Gates (must pass):**
- `seed_variance == FIXED` (or strictly incremented for dynamic frames: `42 + idx`).
- `style_match_threshold >= 0.80`: Visually evaluate styled elements against a master reference vector.

**Default tools:**
- `Ollama/Qwen3-14B` (primary semantic controller to parse and append details like clothing, color schemes, and lighting to prompts)
- `Python/Random` (fallback deterministic seed generation manager)

**Automation hooks:**
- `validate_X55(job_id)`
- `run_X55(job_id, profile)`
- `score_X55(job_id)`
- `retry_X55(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Define and maintain a character/scene specification sheet, feeding it systematically into prompt generation pipelines so characters and assets do not shift between cuts.

### When to run this chapter
- During the planning and script-packaging phase (Chapter X15).
- Immediately before invoking parallel scene generation steps.

### Default steps (golden path)
1) Extract visual styling elements from `config.style_settings`.
2) Generate a master character reference description via Qwen3.
3) Pre-generate an array of deterministic seed values (e.g. starting at seed 42) and map them to scenes.
4) Formulate enriched image prompts by appending the style block to all generation segments.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/99_logs/X55/continuity_report.json`
- [ ] QC passed: All scenes share style tokens.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X55]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Style Template | `config.style_settings.base_style` | E.g. `"Cinematic, dark mode, high contrast"` |
| Character specs | `config.style_settings.character_details` | Physical traits list |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Continuity Report | `/jobs/<job_id>/99_logs/X55/continuity_report.json` | Mapping of seeds and visual tokens |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.continuity.master_seed` | `42` | Root seed for reproducibility |
| `config.continuity.append_style` | `True` | Automatically inject style suffix to prompt strings |

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Ollama with Qwen3-14B
  - **Version/pin:** Qwen 3 14B JSON mode
  - **Compute notes:** Runs on GPU (8GB VRAM)
  - **Strengths:** Excellent memory retention and parsing of visual tokens.

---

## 5) Procedure (Operator Steps)

### Step 1 — Formulate Prompt Suffix
- **Inputs:** `base_style` setting.
- **Action:**
  - Create string builder code:
    ```python
    def enrich_prompt(raw_prompt, style):
        return f"{raw_prompt}, {style}, highly detailed, 8k resolution"
    ```
- **Expected output:** Unified prompt string.
- **Common failures:** Redundant styling words.
- **Fix:** Filter prompt words to remove duplicate tokens before sending to ComfyUI.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X55(job_id)`: Confirms consistency rules.
- `run_X55(job_id, profile)`: Applies style injections to script steps.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Verify that style enrichment appends tokens correctly.
- **Pass criteria:** Prompts contain both raw concept and style keywords.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Seeds are deterministic (`42 + index`).
- [ ] No stylistic words contradict each other in the final prompts.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `seed_list`
- `injected_token_count`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Style Drift Across Long Sequences
- **Cause:** KSampler random noise seeds drifting too far.
- **Fix:** Keep CFG low (1.0-2.0) for Schnell/GGuf models and use a single fixed seed for all background scenes, varying only subject prompt tokens.

---

## 11) Examples (Copy-paste)
- Example output json structure:
  ```json
  {
    "master_seed": 42,
    "scenes": [
      {"scene_index": 0, "seed": 42, "style_suffix": "Cinematic, dark mode"},
      {"scene_index": 1, "seed": 43, "style_suffix": "Cinematic, dark mode"}
    ]
  }
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X55/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Wrote prompt and seed continuity guidelines.
