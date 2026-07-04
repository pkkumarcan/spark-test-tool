---
chapter_id: X75
title: "Release Checklist"
layer: "Publishing"
status: "implemented"
purpose: "Final safety verification checklist before video goes public"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "15m"
inputs:
  - "publish_package.json"
outputs:
  - "release_checklist_report.json"
qc_gates:
  - "ad_disclosure_present == True"
default_tools:
  primary: "python/checklist_validator"
  fallback: "Manual tick check"
smoke_tests:
  - "A_minimal"
hooks:
  validate: "validate_X75"
  run: "run_X75"
  score: "score_X75"
  retry: "retry_X75"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED"
  max_retries: 2
---

# X75 — Release Checklist

## Chapter Card
**Chapter:** `X75 — Release Checklist`  
**Layer:** `Publishing`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Verify ad disclosures, title bounds, and audio sync before public release.  
**Last Verified:** 2026-06-17  

---

## 1) Golden Path Checklist
- [ ] Title length is under 100 characters.
- [ ] Description contains sponsored disclosure tags if affiliate links are included.
- [ ] Rendered thumbnail contains zero spelling typos.
- [ ] Audio volume matches target standard loudness.

---

## 2) Change Log (Chapter Local)

- 2026-06-17 — Defined final release checklists.
