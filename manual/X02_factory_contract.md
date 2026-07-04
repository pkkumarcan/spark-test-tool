---
chapter_id: X02
title: "Factory Contract"
layer: "Foundation"
status: "implemented"
purpose: "Define job manifest, folder schema, naming conventions, and DoD"
owner: "Human/Agent"
last_updated: "2026-06-19"
estimated_time: "2h"
inputs:
  - "job_type"
  - "params"
outputs:
  - "validation_result"
qc_gates:
  - "validate_inputs"
  - "validate_outputs"
default_tools:
  primary: "factory_contract.py"
smoke_tests:
  - "validate_inputs"
  - "validate_outputs"
hooks:
  validate: "validate_X02"
  run: "run_X02"
  score: "score_X02"
  retry: "retry_X02"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED"
  max_retries: 3
---

# X02 — Factory Contract

## Chapter Card
**Chapter:** `X02 — Factory Contract`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose:** Define job manifest, folder schema, naming conventions, and DoD  
**Last Verified:** 2026-06-19

---

## 1) Quickstart (Golden Path)

### Goal
Enforce structured input validation schemas, proper output naming formatting, and verify complete output generation (Definition of Done) for core media pipelines.

### When to run
- Prior to starting long-running GPU tasks (e.g. video, audio, image generation).
- Post-generation to verify output integrity.

### Golden Path Steps
1) Define the input parameters dictionary.
2) Run `validate_inputs(job_type, params)` in [factory_contract.py](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/factory_contract.py).
3) Trigger generation pipeline.
4) Run `validate_outputs(job_type, job_id, output_dir)` to verify output compliance.

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Job Type | `job_type` | E.g. `video_generate`, `image_generate`, `music_generate` |
| Parameters | `params` | Key-value dictionary containing prompt and options |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Validation Status | Boolean + Msg | Indicates compliance with schemas |

### Definition of Done (DoD)
- The output file must exist in `/app/output`.
- The filename must strictly follow `{job_id}.{ext}`.
- File size must be greater than 0 bytes.

---

## 3) Tooling (Approved Stack)

### Primary (default)
- **Tool:** Python script-based validation module [factory_contract.py](file:///home/pkkumar/AGGY/spark-test-tool/app/backends/factory_contract.py)

---

## 4) Troubleshooting

### Issue 1 — DoD Failed: Output file not found
- **Cause:** Video generation or other task failed silently, or output path was misconfigured.
- **Fix:** Check ComfyUI/Whisper/F5-TTS container logs and verify output directories match mapping.

---

## 5) Change Log

- 2026-06-19 — Implemented factory validation code and updated documentation.
