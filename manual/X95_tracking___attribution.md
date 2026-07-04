---
chapter_id: X95
title: "Tracking & Attribution"
layer: "Governance"
status: "implemented"
purpose: "Govern UTM parameter schemas, conversion pixels, and source attribution routing"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "30m"
inputs:
  - "config.tracking_settings"
  - "funnel_manifest.json"
outputs:
  - "attribution_report.json"
qc_gates:
  - "utm_structure_valid == True"
  - "pixel_endpoint_reachable == True"
default_tools:
  primary: "python/urllib/parse"
  fallback: "Manual attribution verification spreadsheet"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X95"
  run: "run_X95"
  score: "score_X95"
  retry: "retry_X95"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X95 — Tracking & Attribution

## Chapter Card
**Chapter:** `X95 — Tracking & Attribution`  
**Layer:** `Governance`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Ensure all promotional links carry strict UTM parameters and route conversion pixels correctly.  
**Last Verified:** 2026-06-17  

**Inputs (files/keys):**
- `config.tracking_settings` (UTM mapping rules, campaign structures)
- `/jobs/<job_id>/publish/funnel_manifest.json`

**Outputs (files):**
- `/jobs/<job_id>/publish/attribution_report.json`

**Quality Gates (must pass):**
- `utm_structure_valid == True`: Ensures all parameters (`utm_source`, `utm_medium`, `utm_campaign`, `utm_content`) are present and conform to lowercase-dashed naming guidelines.
- `pixel_endpoint_reachable == True`: Confirms the server-side pixel tracking API responds with HTTP 200/201.

**Default tools:**
- `python/urllib/parse` (primary validation mechanism)
- `Manual attribution verification spreadsheet` (fallback auditing process)

**Automation hooks:**
- `validate_X95(job_id)`
- `run_X95(job_id, profile)`
- `score_X95(job_id)`
- `retry_X95(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-17`  

---

## 1) Quickstart (Golden Path)

### Goal
Parse all target links dynamically generated in the publication package and append standardized tracking tags to attribute campaign performance correctly.

### When to run this chapter
- Immediately after landing pages are finalized (Chapter X94).
- Prior to final publication packages being deployed (Chapter X18/X72).

### Default steps (golden path)
1) Read active links from `/jobs/<job_id>/publish/funnel_manifest.json`.
2) Retrieve tracking schemas from `config.tracking_settings`.
3) Apply UTM tag generation rules to produce marked URLs.
4) Validate structured queries against the UTM syntax schema.
5) Record output links and verification flags to `/jobs/<job_id>/publish/attribution_report.json`.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/publish/attribution_report.json`
- [ ] QC passed: UTM validity check returns `True`.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X95]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Target URL | `funnel_manifest.json -> landing_page_url` | Base URL to tag |
| Channel Meta | `job_manifest.json -> metadata.channel_id` | Tracking identifier |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Attribution Report | `/jobs/<job_id>/publish/attribution_report.json` | Verification & link table |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### UTM Tag Schema Rules
- **utm_source**: Lowercase only. Maps to platform (e.g. `youtube`, `tiktok`).
- **utm_medium**: Lowercase only. Maps to formats (e.g. `video-desc`, `pinned-comment`).
- **utm_campaign**: Lowercase, words joined by dashes (e.g. `spark-launch-v1`).
- **utm_content**: Video ID or timestamp key (e.g. `video-2468`).

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Python Standard `urllib.parse`
  - **Version/pin:** Python 3.10+ Standard Library
  - **Compute notes:** CPU execution (instantaneous).
  - **Strengths:** Robust URL parsing, query parameter injection, and safe encoding.

---

## 5) Procedure (Operator Steps)

### Step 1 — Inject Tracking Parameters
- **Inputs:** Base URL and tracking parameters.
- **Action:** Execute the tagging logic to join parameters cleanly without duplicating `?` marks.
- **Expected output:** Returns string like `https://example.com/optin?utm_source=youtube&utm_medium=video-desc&utm_campaign=spark-launch-v1&utm_content=vid-abc`.
- **Common failures:** Doubled question marks or broken query separators (`&`).
- **Fix:** Use `urllib.parse.urlparse` and `urllib.parse.urlunparse` instead of simple string concatenation.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X95(job_id)`: Checks for incoming link configurations.
- `run_X95(job_id, profile)`: Runs the tagging validator script.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Verify that a standard URL gets query variables appended correctly.
- **Pass criteria:** Parsed result contains all target UTM keys.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] All target URLs have valid scheme (`https://`).
- [ ] No tracking tags contain spaces or special uppercase characters.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `total_tagged_links`
- `attribution_quality_index`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Query parameters lost on redirect
- **Cause:** Landing page router strips query strings during trailing slash redirect (e.g. `/optin` -> `/optin/`).
- **Fix:** Direct links to the exact final trailing slash URL path.

---

## 11) Examples (Copy-paste)
- Python tag builder:
  ```python
  from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

  def add_utm(url, params):
      url_parts = list(urlparse(url))
      query = dict(parse_qsl(url_parts[4]))
      query.update(params)
      url_parts[4] = urlencode(query)
      return urlunparse(url_parts)
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X95/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-17 — Created UTM tagging standard and ingestion pipeline rules.
