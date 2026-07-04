---
chapter_id: X53
title: "Image→Video Workflows"
layer: "Video"
status: "implemented"
purpose: "Animate static images into video clips using ComfyUI i2v models"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "25m"
inputs:
  - "Source image (base64 or path)"
  - "Motion prompt"
  - "Model selection"
outputs:
  - "Animated video (MP4)"
  - "Job ID for tracking"
qc_gates:
  - "Video generated from image"
  - "Motion matches prompt"
default_tools:
  primary: "ComfyUI i2v models"
  fallback: "Manual animation"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X53"
  run: "run_X53"
  score: "score_X53"
  retry: "retry_X53"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X53 — Image→Video Workflows

## Chapter Card
**Chapter:** `X53 — Image→Video Workflows`  
**Layer:** `Video`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Animate static images into video clips using ComfyUI i2v models.  
**Last Verified:** 2026-06-15

**Actual Implementation:**
- **File:** `app/backends/comfyui_video.py` (804 lines)
- **Endpoint:** `POST /api/video/generate`
- **Mode:** `i2v` (image-to-video)
- **Test Frame:** `POST /api/video/test-frame`

**Supported Models:**
| Model | Type | Best For |
|-------|------|----------|
| `cogvideox_5b_i2v_bf16.safetensors` | CogVideoX | People, characters |
| `wan2.2_14b_q4.gguf` | Wan 2.2 | General animation |
| `ltx-2.3-22b-dev-Q4_K_M.gguf` | LTX | Fast generation |

**Quality Gates:**
- Gate 1: Video generated from image
- Gate 2: Motion matches prompt description

---

## 1) Quickstart (Golden Path)

### Goal
Animate a static image into a video clip.

### When to run
- For keyframe animation
- For product visualization
- For character animation

### Golden Path Steps
1) **Test frame (optional)**:
   ```bash
   curl -X POST http://localhost:5050/api/video/test-frame \
     -F "file=@image.png" \
     -F "model=cogvideox_5b_i2v_bf16.safetensors"
   ```
   Expected: Test frame processed

2) **Generate i2v video**:
   ```bash
   curl -X POST http://localhost:5050/api/video/generate \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Gentle camera pan showing the scene",
       "model": "cogvideox_5b_i2v_bf16.safetensors",
       "mode": "i2v",
       "start_image": "data:image/png;base64,...",
       "width": 768,
       "height": 448,
       "frames": 25
     }'
   ```
   Expected: Job ID returned

3) **Poll and download**:
   - Poll `/api/jobs/{job_id}` until completed
   - Download video from result URL

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Source image | `start_image` | Base64 data URL or `/output/` path |
| Prompt | `prompt` | Motion description |

### Optional Inputs
| Input | Path/Key | Default | Notes |
|-------|----------|---------|-------|
| Model | `model` | `cogvideox_5b_i2v_bf16.safetensors` | i2v model |
| Frames | `frames` | 25 | Number of frames |
| Seed | `seed` | random | Reproducibility |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Job ID | Response | For tracking |
| Video URL | Job result | Path to generated video |

---

## 3) Image Input Formats

### Base64 Data URL
```json
{
  "start_image": "data:image/png;base64,iVBORw0KGgo..."
}
```

### Local Output Path
```json
{
  "start_image": "/output/spark_abc12345.png"
}
```

### Direct Base64
```json
{
  "start_image": "iVBORw0KGgo..."
}
```

---

## 4) Procedure (Operator Steps)

### Step 1 — Upload Source Image
- **Inputs:** Image data (base64 or path)
- **Action:** Upload to ComfyUI via `/upload/image`
- **Expected output:** ComfyUI filename
- **Common failures:** Invalid format, file not found
- **Fix:** Verify image data, check file exists

### Step 2 — Build i2v Workflow
- **Inputs:** Image filename, prompt, settings
- **Action:** Construct i2v-specific workflow nodes
- **Expected output:** Valid workflow JSON
- **Common failures:** Missing nodes, wrong model
- **Fix:** Check model compatibility

### Step 3 — Submit to ComfyUI
- **Inputs:** Workflow JSON
- **Action:** POST to ComfyUI `/prompt`
- **Expected output:** Prompt ID
- **Common failures:** ComfyUI error
- **Fix:** Check ComfyUI logs

### Step 4 — Process Result
- **Inputs:** Generated video
- **Action:** Save to output directory
- **Expected output:** MP4 file
- **Common failures:** Encoding error
- **Fix:** Check video codec support

---

## 5) Troubleshooting

### Issue 1 — "Image upload failed"
- **Cause:** Invalid image format or data
- **Fix:** Convert to PNG, verify base64
- **Prevention:** Validate before upload

### Issue 2 — "No motion generated"
- **Cause:** Prompt too vague or wrong model
- **Fix:** Use more descriptive prompt
- **Prevention:** Test with known-good prompts

### Issue 3 — "Video flickers"
- **Cause:** Low frame count or bad seed
- **Fix:** Increase frames, try different seed
- **Prevention:** Use recommended settings

### Issue 4 — "GPU out of memory"
- **Cause:** High resolution + many frames
- **Fix:** Reduce resolution or frames
- **Prevention:** Check VRAM requirements

---

## 6) Change Log

- 2026-06-15 — Initial implementation with actual codebase content