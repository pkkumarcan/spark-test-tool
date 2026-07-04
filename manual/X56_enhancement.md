---
chapter_id: X56
title: "Technical Enhancement"
layer: "Video"
status: "implemented"
purpose: "Upscale images and execute lip-sync audio-video alignments"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "15m"
inputs:
  - "image_url"
  - "video_url"
  - "audio_url"
outputs:
  - "upscaled_image"
  - "lipsynced_video"
qc_gates:
  - "file_existence == True"
  - "api_response_code == 200"
default_tools:
  primary: "FastAPI / postprocess"
  fallback: "Manual copy"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X56"
  run: "run_X56"
  score: "score_X56"
  retry: "retry_X56"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X56 — Technical Enhancement

## Chapter Card
**Chapter:** `X56 — Technical Enhancement`  
**Layer:** `Video`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Expose APIs to upscale frames and apply lip-sync (LatentSync) processing to video assets.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- Image URLs, video URLs, and audio URLs from previous steps.

**Outputs (files):**
- `/jobs/<job_id>/04_video/enhanced/` outputs (MP4/PNG files).

**Quality Gates (must pass):**
- `file_existence == True`: Enhanced outputs must be saved to the target directory.
- `api_response_code == 200`: Postprocess service must return a success response code.

**Default tools:**
- `FastAPI / postprocess` (Primary automation coordinator)
- `Real-ESRGAN / LatentSync` (Underlying models, currently mocked/stubbed in backend)

**Automation hooks:**
- `validate_X56(job_id)`
- `run_X56(job_id, profile)`
- `score_X56(job_id)`
- `retry_X56(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Trigger upscaling and lip-sync alignment via the FastAPI backends.

### When to run this chapter
- Immediately after scene generation (Chapter X52/X53).
- Before compiling the final output cuts.

### Default steps (golden path)
1) Send a POST request to `/api/postprocess/upscale` specifying the image file and scale factor.
2) Send a POST request to `/api/postprocess/lipsync` specifying the video and voiceover URLs.
3) Retrieve the output paths from the response dictionary.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/03_images/ups_*` or `/jobs/<job_id>/04_video/sync_*`
- [ ] QC passed: Files exist and have non-zero sizes.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X56]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Image URL | `image_url` | Target image to upscale |
| Scale factor | `scale` | 2 or 4 (default: 4) |
| Video URL | `video_url` | Target video for lipsyncing |
| Audio URL | `audio_url` | Target audio for lipsyncing |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Enhanced File | `/jobs/<job_id>/...` | Path to generated asset |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.postprocess.scale` | `4` | Scale factor for image upscaling |

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** FastAPI Backend (`postprocess.py`)
  - **Version/pin:** Python 3.11+
  - **Compute notes:** Runs synchronously on CPU in simulated mode.
  - **Strengths:** Light resource utilization.
  - **Weaknesses:** Underlying heavy neural upscaler models are stubbed to prevent OOM in resource-constrained environments.

---

## 5) Procedure (Operator Steps)

### Step 1 — Call Upscale
- **Inputs:** `image_url`
- **Action:** Send a JSON payload to `/api/postprocess/upscale`.
- **Expected output:** Returns a JSON response containing `output_url`.
- **Common failures:** Original file does not exist.
- **Fix:** Verify file path matches public static endpoints.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X56(job_id)`: Verifies files before upscaling.
- `run_X56(job_id, profile)`: Dispatches upscale/lipsync tasks.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Validate endpoint responds.
- **Input:** Dummy paths.
- **Steps:** Perform API POST to the upscale route.
- **Pass criteria:** Returns status code 200.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Output URL is accessible.
- [ ] Image format remains PNG.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `runtime_seconds`
- `scale`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Returns Placeholder Image
- **Cause:** Input file could not be found, causing fallback copy.
- **Fix:** Ensure the input URL starts with `/output/` and exists inside the workbench output directory.

---

## 11) Examples (Copy-paste)
- Example python call:
  ```python
  import httpx
  r = httpx.post("http://localhost:8000/api/postprocess/upscale", json={"image_url": "/output/myimg.png", "scale": 4})
  print(r.json())
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X56/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Documented endpoint stubs and input/output contracts.