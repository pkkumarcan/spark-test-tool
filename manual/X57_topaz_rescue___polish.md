---
chapter_id: X57
title: "Topaz Rescue & Polish"
layer: "Video"
status: "implemented"
purpose: "Rescue low-quality or artifact-heavy video clips and apply final visual polish"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - "corrupted_or_lowres_scene.mp4"
outputs:
  - "polished_scene.mp4"
qc_gates:
  - "noise_reduction_level >= 0.70"
  - "motion_smoothness == PASSED"
default_tools:
  primary: "Topaz Video AI CLI"
  fallback: "FFmpeg (hqdn3d filter)"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X57"
  run: "run_X57"
  score: "score_X57"
  retry: "retry_X57"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X57 — Topaz Rescue & Polish

## Chapter Card
**Chapter:** `X57 — Topaz Rescue & Polish`  
**Layer:** `Video`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Repair rendering artifacts, upscale low-resolution scenes, and interpolate frames for smooth motion.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `/jobs/<job_id>/04_video/raw_scenes/scene_<index>.mp4`

**Outputs (files):**
- `/jobs/<job_id>/04_video/polished/scene_polished_<index>.mp4`

**Quality Gates (must pass):**
- `noise_reduction_level >= 0.70`: High frequency digital noise must be suppressed.
- `motion_smoothness == PASSED`: Frame rate must be successfully interpolated to 50fps/60fps without block artifacts.

**Default tools:**
- `Topaz Video AI CLI` (primary command-line processor for motion-compensated upscaling)
- `FFmpeg (hqdn3d filter)` (fallback lightweight denoiser and stabilizer)

**Automation hooks:**
- `validate_X57(job_id)`
- `run_X57(job_id, profile)`
- `score_X57(job_id)`
- `retry_X57(job_id, strategy)`

**Smoke test time:** `~10 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Polish generated video scenes by upscaling to 4K resolution and applying AI frame interpolation (Chronos or Apollo models).

### When to run this chapter
- When generated outputs exhibit structural wobbling or low resolution.
- As a final rendering step before full video assembly.

### Default steps (golden path)
1) Identify the low-quality video clip inside `/jobs/<job_id>/04_video/raw_scenes/`.
2) Run the Topaz CLI command using the Proteus model for detail recovery.
3) Apply Chronos Fast model to interpolate frame rates to a stable 60 fps.
4) Save the polished file to the output folder.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/04_video/polished/scene_polished_0.mp4`
- [ ] QC passed: Frame count has doubled (for 60fps interpolation) and resolution is 3840x2160.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X57]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Low-res video | `/jobs/<job_id>/04_video/raw_scenes/*.mp4` | Video clip to polish |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Polished Video | `/jobs/<job_id>/04_video/polished/*.mp4` | High-fidelity output file |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.topaz.model` | `"prob-4"` | Proteus Auto v4 detail recovery model |
| `config.topaz.interpolation` | `"chr-3"` | Chronos v3 motion interpolation model |

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Topaz Video/Photo AI remote service
  - **Endpoint:** `http://10.0.0.162:5060` (Node B / Windows host)
  - **Version/pin:** `>=4.x` (native Windows execution)
  - **Compute notes:** Runs on Node B's GPUs (RTX 3060 / 3060 Ti)
  - **Features:** Dynamic path resolution for `ffmpeg.exe` and `tpai.exe`, asynchronous subprocess execution, and streaming logs capture.

---

## 5) Procedure (Operator Steps)

### Step 1 — Dispatch Task to Node B Topaz Service
- **Inputs:** `scene_0.mp4`
- **Action:**
  - Send a POST request to the remote Topaz service on Node B (`http://10.0.0.162:5060`) with the target video parameters:
    ```bash
    curl -X POST "http://10.0.0.162:5060/run" \
      -H "Content-Type: application/json" \
      -d '{
        "input_path": "C:\\projects\\raw_scenes\\scene_0.mp4",
        "output_path": "C:\\projects\\polished\\scene_polished_0.mp4",
        "model": "prob-4",
        "scale": 2
      }'
    ```
- **Expected output:** Returns a JSON response indicating background task startup, log streaming handles, or immediate completion details.
- **Common failures:** License check fails or Node B service is offline.
- **Fix:** Fallback to local Node A FFmpeg denoising pipeline:
  ```bash
  ffmpeg -i scene_0.mp4 -vf "hqdn3d=2.0:1.5:3.0:2.25" polished_0.mp4
  ```

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X57(job_id)`: Checks license environment variable.
- `run_X57(job_id, profile)`: Runs the VEAI enhancement process.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Run the FFmpeg fallback denoiser on a test clip.
- **Pass criteria:** Polished output file exists.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Output video resolution is at least 1920x1080.
- [ ] No visual blockiness on motion boundaries.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `runtime_seconds`
- `upscale_ratio`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Processing Time Too Slow
- **Cause:** GPU acceleration not correctly mapped inside Docker or system wrappers.
- **Fix:** Pass `--device /dev/nvidia0` during runtime allocations.

---

## 11) Examples (Copy-paste)
- Example FFmpeg fallback pipeline command:
  ```bash
  ffmpeg -y -i scene.mp4 -vf "hqdn3d=3.0:3.0:4.0:4.0,unsharp=5:5:0.8:5:5:0.0" output_polished.mp4
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X57/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Wrote Topaz CLI and FFmpeg fallback rescue guidelines.
