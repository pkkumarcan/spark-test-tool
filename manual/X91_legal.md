---
chapter_id: X91
title: "Legal/IP/Compliance"
layer: "Governance"
status: "implemented"
purpose: "Govern copyright verification, trademark compliance, and licensing checks for generated media assets"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - "job_manifest.json"
outputs:
  - "compliance_report.json"
qc_gates:
  - "copyright_infringement_risk == LOW"
  - "trademark_check == PASSED"
default_tools:
  primary: "Ollama/Llava-v1.6 (vision auditing)"
  fallback: "Manual IP Audit Checklist"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X91"
  run: "run_X91"
  score: "score_X91"
  retry: "retry_X91"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X91 — Legal/IP/Compliance

## Chapter Card
**Chapter:** `X91 — Legal/IP/Compliance`  
**Layer:** `Governance`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Ensure all generated text, audio, and visual outputs comply with IP, copyright, and platform safety guidelines.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `/jobs/<job_id>/job_manifest.json` (prompt inputs, generated script narration)
- `/jobs/<job_id>/03_images/` (rendered visual layers)

**Outputs (files):**
- `/jobs/<job_id>/99_logs/X91/compliance_report.json`

**Quality Gates (must pass):**
- `copyright_infringement_risk == LOW`: Prompts must not request copyrighted fictional characters (e.g. Disney, Marvel) or trademarked brand names.
- `trademark_check == PASSED`: Output text and images must be free of unauthorized brand logo inclusions.

**Default tools:**
- `Ollama/Llava-v1.6 (vision auditing)` (primary visual compliance scanner)
- `Manual IP Audit Checklist` (fallback auditor review process)

**Automation hooks:**
- `validate_X91(job_id)`
- `run_X91(job_id, profile)`
- `score_X91(job_id)`
- `retry_X91(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Audit prompts and output frames to confirm they are safe for commercial publishing channels.

### When to run this chapter
- Immediately after script writing (Chapter X13) and image generation (Chapter X42).
- Prior to final deliverables bundle creation (Chapter X67).

### Default steps (golden path)
1) Scan `job_manifest.json` prompt inputs against a localized blacklist of copyrighted/trademarked words.
2) Send generated thumbnails and scene frames to the Llava visual auditor model.
3) Request an object-detection check for unauthorized trademarks or commercial logos.
4) Write audit results to `compliance_report.json`.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/99_logs/X91/compliance_report.json`
- [ ] QC passed: Compliance risk score is flagged as `passed`.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X91]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Target Prompts | `job_manifest.json` | All text prompts used for generation |
| Output Images | `/jobs/<job_id>/03_images/*.png` | Rendered images to scan |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Audit Report | `/jobs/<job_id>/99_logs/X91/compliance_report.json` | JSON report of audit findings |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Prompt Blacklist
The system rejects prompts containing the following terms:
- Copyrighted characters (e.g. "Mickey Mouse", "Batman").
- Direct corporate brands (unless explicitly whitelisted for reviews).

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Ollama / Llava-v1.6
  - **Version/pin:** `llava:13b`
  - **Compute notes:** Runs on GPU (requires 8GB VRAM).
  - **Strengths:** High semantic accuracy for identifying brand logos in graphics.

---

## 5) Procedure (Operator Steps)

### Step 1 — Run Text Compliance Check
- **Inputs:** `job_manifest.json`
- **Action:** Execute regex checks against the blacklisted character terms:
  ```python
  import re
  BLACKLIST = ["disney", "marvel", "nintendo"]
  def check_text(text):
      for word in BLACKLIST:
          if re.search(r'\b' + re.escape(word) + r'\b', text.lower()):
              return False
      return True
  ```
- **Expected output:** Returns `True` (safe).
- **Common failures:** False positives on homonyms.
- **Fix:** Manually override warning in `compliance_report.json` if clean.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X91(job_id)`: Checks for manifest files.
- `run_X91(job_id, profile)`: Dispatches text/image checks.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Scan a clean text string.
- **Pass criteria:** Returns status `passed`.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] No trademark logos in generated B-roll.
- [ ] No music tracks violate YouTube Content ID rules.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `compliance_score`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Llava Model Not Pulled
- **Cause:** Local Ollama server is missing the Llava-v1.6 weights.
- **Fix:** Run `ollama pull llava:13b` to pre-stage the vision check pipeline.

---

## 11) Examples (Copy-paste)
- Example Python check routine:
  ```python
  import json
  with open("manifest.json") as f:
      data = json.load(f)
      print("Prompts are clean:", all(word not in str(data) for word in ["disney"]))
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X91/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Created compliance and IP audit chapter.
