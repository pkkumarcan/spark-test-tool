---
chapter_id: X52
title: "Text→Video Workflows"
layer: "Video"
status: "implemented"
purpose: "Generate video clips from text prompts using ComfyUI video models"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - "Text prompt"
  - "Model selection"
  - "Resolution settings"
  - "Frame count"
outputs:
  - "Video file (MP4)"
  - "Job ID for tracking"
qc_gates:
  - "Video generated successfully"
  - "Video plays correctly"
default_tools:
  primary: "ComfyUI + Wan 2.2 (wan2.2_14b_q4.gguf)"
  fallback: "LTX, CogVideoX, Allegro"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X52"
  run: "run_X52"
  score: "score_X52"
  retry: "retry_X52"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X52 — Text→Video Workflows

## Chapter Card
**Chapter:** `X52 — Text→Video Workflows`  
**Layer:** `Video`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Generate video clips from text prompts using ComfyUI video models.  
**Last Verified:** 2026-06-15

**Actual Implementation:**
- **File:** `app/backends/comfyui_video.py` (804 lines)
- **Endpoint:** `POST /api/video/generate`
- **Mode:** `t2v` (text-to-video)
- **Background Job:** Returns job_id, poll `/api/jobs/{job_id}`

**Supported Models:**
| Model | Type | VRAM | Notes |
|-------|------|------|-------|
| `wan2.2_14b_q4.gguf` | Wan 2.2 MoE | ~12GB | Default, high quality |
| `ltx-2.3-22b-dev-Q4_K_M.gguf` | LTX | ~16GB | Fast, good quality |
| `cogvideox_5b_i2v_bf16.safetensors` | CogVideoX | ~12GB | Good for i2v |
| `allegro_v1_0_fp8.safetensors` | Allegro | ~8GB | Fast FP8 |
| `dreamshaper_8.safetensors` | AnimateDiff | ~4GB | SD 1.5 based |

**Quality Gates:**
- Gate 1: Video generated successfully
- Gate 2: Video plays correctly

---

## 1) Quickstart (Golden Path)

### Goal
Generate a video clip from a text prompt.

### When to run
- For b-roll generation
- For social media content
- For visual effects

### Golden Path Steps
1) **Submit video generation**:
   ```bash
   curl -X POST http://localhost:5050/api/video/generate \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Ocean waves crashing on rocky shore at sunset",
       "model": "wan2.2_14b_q4.gguf",
       "width": 768,
       "height": 448,
       "frames": 25,
       "mode": "t2v"
     }'
   ```
   Expected: `{"job_id": "vid_abc12345", "status": "pending"}`

2) **Poll for completion**:
   ```bash
   curl http://localhost:5050/api/jobs/vid_abc12345
   ```
   Expected: Status changes to "completed" with result URL

3) **Download video**:
   - Result contains `video_url` field
   - Download from output directory

### Done looks like
- [ ] Job submitted successfully
- [ ] Job completed without errors
- [ ] Video file generated
- [ ] Video plays correctly

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Prompt | `prompt` | Text description of video |

### Optional Inputs
| Input | Path/Key | Default | Notes |
|-------|----------|---------|-------|
| Model | `model` | `wan2.2_14b_q4.gguf` | Video model |
| Width | `width` | 768 | Video width |
| Height | `height` | 448 | Video height |
| Frames | `frames` | 25 | Number of frames |
| Mode | `mode` | `t2v` | t2v, i2v, interpolation |
| Seed | `seed` | random | Reproducibility |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Job ID | Response | For tracking |
| Video URL | Job result | Path to generated video |

### Definition of Done (DoD)
Job submitted + video generated + file playable.

---

## 3) Config & Standards

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `COMFYUI_URL` | `http://host.docker.internal:8188` | ComfyUI endpoint |
| `OUTPUT_DIR` | `/app/output` | Where to save videos |

### Default Settings
- **Model:** wan2.2_14b_q4.gguf
- **Resolution:** 768x448
- **Frames:** 25
- **Steps:** 20
- **CFG:** 6.0 (6.0 for most models, 1.0 for LTX)

---

## 4) Model Selection Guide

### For B-Roll (General footage)
- **Wan 2.2** — High quality, good motion
- **LTX** — Fast, decent quality

### For Character Animation
- **CogVideoX** — Good for people/characters
- **Allegro** — Fast, FP8 optimized

### For Stylized Content
- **AnimateDiff (Dreamshaper)** — SD 1.5 style, fast

---

## 5) Procedure (Operator Steps)

### Step 1 — Validate Input
- **Inputs:** Request body
- **Action:** Check model is supported, validate parameters
- **Expected output:** Valid request
- **Common failures:** Unsupported model, invalid dimensions
- **Fix:** Check `SUPPORTED_VIDEO_MODELS` list

### Step 2 — Submit Background Job
- **Inputs:** Validated parameters
- **Action:** Create job in job_store, start async task
- **Expected output:** Job ID returned
- **Common failures:** Job store error
- **Fix:** Check SQLite database

### Step 3 — Generate Video
- **Inputs:** Job parameters
- **Action:** Build workflow, submit to ComfyUI
- **Expected output:** Video file in output directory
- **Common failures:** GPU OOM, ComfyUI timeout
- **Fix:** Reduce frames, check GPU memory

### Step 4 — Update Job Status
- **Inputs:** Generation result
- **Action:** Update job_store with completion status
- **Expected output:** Job marked as completed
- **Common failures:** Database error
- **Fix:** Check file permissions

---

## 6) Troubleshooting

### Issue 1 — "GPU out of memory"
- **Cause:** Video generation requires significant VRAM
- **Fix:** Reduce resolution or frame count
- **Prevention:** Check GPU before starting

### Issue 2 — "Video generation timeout"
- **Cause:** Complex prompt or busy GPU
- **Fix:** Wait and retry, use faster model
- **Prevention:** Monitor job queue

### Issue 3 — "Unsupported model"
- **Cause:** Model not in supported list
- **Fix:** Use one of the supported models
- **Prevention:** Check model documentation

### Issue 4 — "Video quality poor"
- **Cause:** Low frames or wrong model
- **Fix:** Increase frames, try different model
- **Prevention:** Test with sample prompts

---

## 7) Change Log

- 2026-06-15 — Initial implementation with actual codebase content