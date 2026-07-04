---
chapter_id: X94
title: "Funnels & Products"
layer: "Governance"
status: "implemented"
purpose: "Govern lead magnets, landing pages, email sequence templates, and product offer delivery"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "1h"
inputs:
  - "config.funnel_settings"
outputs:
  - "funnel_manifest.json"
qc_gates:
  - "landing_page_responsive == True"
  - "optin_form_active == True"
default_tools:
  primary: "FastAPI / static router"
  fallback: "GitHub Pages / Jekyll"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X94"
  run: "run_X94"
  score: "score_X94"
  retry: "retry_X94"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X94 — Funnels & Products

## Chapter Card
**Chapter:** `X94 — Funnels & Products`  
**Layer:** `Governance`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Automate lead generation, landing page deployment, and follow-up email campaigns.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `config.funnel_settings` (product templates, email copy blocks, static assets)

**Outputs (files):**
- `/jobs/<job_id>/publish/funnel_manifest.json`

**Quality Gates (must pass):**
- `landing_page_responsive == True`: Verify HTML layout rendering on mobile vs desktop.
- `optin_form_active == True`: Submit API endpoint checks to ensure user lead forms are capturing fields.

**Default tools:**
- `FastAPI / static router` (primary landing page host)
- `GitHub Pages / Jekyll` (fallback static landing page hosting)

**Automation hooks:**
- `validate_X94(job_id)`
- `run_X94(job_id, profile)`
- `score_X94(job_id)`
- `retry_X94(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Configure and deploy a lead capture page and connect it to automated follow-up sequences.

### When to run this chapter
- Instantly after the video publishing packages draft is finalized.
- When creating a campaign launch.

### Default steps (golden path)
1) Read campaign configuration details from `config.funnel_settings`.
2) Deploy the static HTML landing template to `/app/static/funnels/`.
3) Verify form endpoints are bound to the database.
4) Write delivery file URLs to `funnel_manifest.json`.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/publish/funnel_manifest.json`
- [ ] QC passed: Form captures test submission successfully.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X94]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Target Campaign | `config.funnel_settings.campaign_id` | Unique identifier |
| Email templates | `config.funnel_settings.emails` | HTML/txt email body blocks |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Funnel Manifest | `/jobs/<job_id>/publish/funnel_manifest.json` | Mappings of landing page and leads DB |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Layout Rules
- Simple, high-contrast CTA buttons.
- Standard form inputs: Name and Email Address.

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** FastAPI Static Files Router
  - **Version/pin:** FastAPI 0.115+
  - **Compute notes:** Runs on CPU (fast server-side routing).

---

## 5) Procedure (Operator Steps)

### Step 1 — Deploy Landing Canvas
- **Inputs:** Static html template.
- **Action:** Copy file to `app/static/index.html`.
- **Expected output:** Local server endpoint loads template.
- **Common failures:** Pathing errors for CSS stylesheets.
- **Fix:** Enforce absolute links (`/static/css/...`) instead of relative paths.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X94(job_id)`: Checks for templates.
- `run_X94(job_id, profile)`: Deploys static files.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Verify localhost serving.
- **Pass criteria:** Server returns HTTP 200 on landing asset endpoint.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Optin form submission captures data.
- [ ] No grammar errors in body copy.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `conversion_rate`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Form Submissions Fail
- **Cause:** CORS block on POST handler routes.
- **Fix:** Update `ALLOWED_ORIGINS` to include the landing page host domain.

---

## 11) Change Log (Chapter Local)

- 2026-06-15 — Wrote landing page and email funnel integration steps.
