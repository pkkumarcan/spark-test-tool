---
chapter_id: X72
title: "Upload Package Generator"
layer: "Publishing"
status: "implemented"
purpose: "Compile rendering deliverables, thumbnails, descriptions, and tags into publishing packages"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "15m"
inputs:
  - "job_manifest.json"
outputs:
  - "publish_package.json"
qc_gates:
  - "thumbnail_exists == True"
  - "video_duration_matched == True"
default_tools:
  primary: "python/publishing"
  fallback: "Manual package compile"
smoke_tests:
  - "A_minimal"
hooks:
  validate: "validate_X72"
  run: "run_X72"
  score: "score_X72"
  retry: "retry_X72"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X72 — Upload Package Generator

## Chapter Card
**Chapter:** `X72 — Upload Package Generator`  
**Layer:** `Publishing`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Generate standardized packaging bundles containing video assets, thumbnails, and descriptions.  
**Last Verified:** 2026-06-17  

**Inputs (files/keys):**
- `/jobs/<job_id>/job_manifest.json` (compiled deliverables references)

**Outputs (files):**
- `/jobs/<job_id>/publish/publish_package.json`

**Quality Gates (must pass):**
- `thumbnail_exists == True`: Check that the finalized JPG/PNG thumbnail is packed.
- `video_duration_matched == True`: Check that the video file plays without truncation.

---

## 1) Quickstart (Golden Path)

### Goal
Amalgamate video render paths, descriptions, tags, and thumbnails into a single deployable package.

### When to run this chapter
- Immediately after video rendering and post-processing (Chapters X57/X67).

### Default steps (golden path)
1) Read outputs from the job manifest.
2) Parse default tags and append campaign description headers.
3) Output metadata and target file paths to `publish_package.json`.

---

## 2) Change Log (Chapter Local)

- 2026-06-17 — Wrote package packaging parameters and verification checklist.
