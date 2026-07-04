---
chapter_id: X54
title: "Video→Video Workflows"
layer: "Video"
status: "implemented"
purpose: "Restyle, enhance, and maintain continuity using keyframe-guided video-to-video generation"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - "input_video.mp4"
  - "style_image.png"
outputs:
  - "restyle_output.mp4"
qc_gates:
  - "motion_score >= 0.6"
  - "style_adherence >= 0.75"
default_tools:
  primary: "ComfyUI/Wan2.2-I2V"
  fallback: "ComfyUI/CogVideoX-5B-I2V"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X54"
  run: "run_X54"
  score: "score_X54"
  retry: "retry_X54"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X54 — Video→Video Workflows

## Chapter Card
**Chapter:** `X54 — Video→Video Workflows`  
**Layer:** `Video`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Restyle videos, interpolate frames, and maintain stylistic continuity using image conditioning.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `/jobs/<job_id>/04_video/raw_scenes/`
- Start and end keyframe images (Pillow/PNG)

**Outputs (files):**
- `/jobs/<job_id>/04_video/v2v_scenes/scene_v2v_<index>.mp4`

**Quality Gates (must pass):**
- `motion_score >= 0.6`: The restyled video must exhibit natural motion vectors without freezing.
- `style_adherence >= 0.75`: The output frames must semantically match the target keyframe styles.

**Default tools:**
- `ComfyUI/Wan2.2-I2V` (primary model for high-resolution fluid video restyling)
- `ComfyUI/CogVideoX-5B-I2V` (fallback model for highly detailed, semantic keyframe mapping)
- `ComfyUI/LTX-2.3` (for ultra-fast preview interpolation)

**Automation hooks:**
- `validate_X54(job_id)`
- `run_X54(job_id, profile)`
- `score_X54(job_id)`
- `retry_X54(job_id, strategy)`

**Smoke test time:** `~15 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Apply style transfer to an existing raw video scene by conditioning the generation on style keyframes or generating interpolations between keyframes.

### When to run this chapter
- When visual consistency across generated raw frames is low.
- When generating transitional scenes (e.g. morphs between two stable image generations).

### Default steps (golden path)
1) Upload the start and optional end keyframe images to the ComfyUI endpoint using the `/upload/image` API.
2) Send a POST request to `/video/generate` specifying the `"mode": "i2v"` or `"mode": "interpolation"`.
3) Select `wan2.2_14b_q4.gguf` or `cogvideox_5b_i2v_bf16.safetensors` as the target model.
4) Poll the ComfyUI server history until completed, and retrieve the restyled video from the output directory.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/04_video/v2v_scenes/scene_v2v_0.mp4`
- [ ] QC passed: Resolution matches target and contains valid video headers.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X54]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Target Model | `model` | E.g. `"wan2.2_14b_q4.gguf"` or `"cogvideox_5b_i2v_bf16.safetensors"` |
| Start Image | `start_image` | Base64 or local output path to guide the style/composition |

### Optional Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| End Image | `end_image` | Guides the final frame (used in interpolation mode) |
| VAE Tiling | `vae_tiling` | Set to `True` for high-res outputs to avoid VRAM exhaustion |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Restyled Video | `/jobs/<job_id>/04_video/v2v_scenes/scene_v2v_<index>.mp4` | Finished style-transferred video clip |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.video.default_v2v_model` | `"wan2.2_14b_q4.gguf"` | Default video-to-video restyler model |
| `config.video.interpolation_steps` | `20` | Sampler steps for frame interpolation |

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** ComfyUI with Wan2.2-I2V
  - **Version/pin:** Wan2.2 GGUF Q4
  - **Compute notes:** Requires 16GB+ VRAM (force VAE tiling for 720p+)
  - **Strengths:** Excellent physical motion representation and minimal structural morphing.

### Alternatives (approved)
- **CogVideoX-5B-I2V** — Recommended for complex visual composition matching.
- **LTX-2.3-22b-dev** — Ideal for rapid 25fps video-audio joint preview generations.

---

## 5) Procedure (Operator Steps)

### Step 1 — Keyframe Conditioning
- **Inputs:** `start_image` and target text `prompt`.
- **Action:**
  - Submit target image to ComfyUI.
  - Bind the `LoadImage` node output to the `WanImageToVideo` / `CogVideoImageEncode` encoder node.
  - Feed the encoded latents to the `KSampler` input.
- **Expected output:** A video output starting with the conditioned image style and developing naturally.
- **Common failures:** Out of Memory (OOM) on VAE decode.
- **Fix:** Enable `vae_tiling: true` in the API payload to force tiled decode operations.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X54(job_id)`: Checks model availability in registry.
- `run_X54(job_id, profile)`: Dispatches the API request to ComfyUI.
- `score_X54(job_id)`: Measures temporal consistency.
- `retry_X54(job_id, strategy)`: Falls back from Wan2.2 to CogVideoX if OOM occurs.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Render a 1-second video interpolation between two tiny squares.
- **Input:** Two 256x256 solid color images.
- **Steps:** Submit payload with `"mode": "interpolation"`, model `"ltx-2.3-22b-dev-Q4_K_M.gguf"`, frames `9`.
- **Pass criteria:** Output file contains valid video payload.
- **If fails:** Check if `LTX23_video_vae_bf16.safetensors` is in the ComfyUI models folder.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Video has no visual flicker or rapid artifact flashing.
- [ ] The first frame matches the style image within a structural similarity limit.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `runtime_seconds`
- `gpu_vram_peak`
- `frame_count`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Sudden Motion Freezing
- **Cause:** Classifier-Free Guidance (CFG) scale set too low.
- **Fix:** Increase CFG value (e.g. from 1.0 to 6.0) for Wan2.2 to enforce prompt tracking.

---

## 11) Examples (Copy-paste)
- Example API Payload for restyling:
  ```json
  {
    "prompt": "cinematic style, vibrant color grading, high detail",
    "mode": "i2v",
    "model": "wan2.2_14b_q4.gguf",
    "start_image": "/output/my_style_frame.png",
    "steps": 20,
    "vae_tiling": true
  }
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Artifacts** in `/jobs/<job_id>/04_video/v2v_scenes/`
2. **Logs** in `/jobs/<job_id>/99_logs/X54/`
3. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Wrote Video-to-Video implementation guidelines.
