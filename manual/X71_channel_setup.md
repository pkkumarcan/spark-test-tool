---
chapter_id: X71
title: "Channel Setup"
layer: "Publishing"
status: "implemented"
purpose: "Configure branding, defaults, and upload credentials"
owner: "Human/Agent"
last_updated: "2026-06-17"
estimated_time: "20m"
inputs:
  - "config.publishing_settings"
outputs:
  - "channel_metadata.json"
qc_gates:
  - "channel_auth_valid == True"
default_tools:
  primary: "google-api-python-client"
  fallback: "Manual YouTube Studio dashboard"
smoke_tests:
  - "A_minimal"
hooks:
  validate: "validate_X71"
  run: "run_X71"
  score: "score_X71"
  retry: "retry_X71"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X71 — Channel Setup

## Chapter Card
**Chapter:** `X71 — Channel Setup`  
**Layer:** `Publishing`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Manage YouTube channel integration parameters and upload configurations.  
**Last Verified:** 2026-06-17  

**Inputs (files/keys):**
- `config.publishing_settings` (channel ID, OAuth secrets)

**Outputs (files):**
- `/jobs/channel_metadata.json` (active channel verification status)

**Quality Gates (must pass):**
- `channel_auth_valid == True`: Ensures oauth tokens are valid and have upload scopes.

**Default tools:**
- `google-api-python-client` (primary API library)
- `Manual YouTube Studio dashboard` (fallback process)

---

## 1) Quickstart (Golden Path)

### Goal
Configure the YouTube API client secrets and authorize credentials to allow automatic uploads.

### When to run this chapter
- During system installation or when channel tokens expire.

### Default steps (golden path)
1) Read API credentials from `.env` or `config.publishing_settings`.
2) Execute the token refresh validation handler.
3) Record status to `/jobs/channel_metadata.json`.

### Done looks like
- [ ] Output exists: `/jobs/channel_metadata.json`
- [ ] QC passed: API authentication state is verified.

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Secrets | `config.publishing_settings.oauth_secrets` | Client secret dict |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Verification | `/jobs/channel_metadata.json` | Token verification output |

---

## 3) Change Log (Chapter Local)

- 2026-06-17 — Wrote channel integration setup guide.
