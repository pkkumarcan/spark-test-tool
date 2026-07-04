---
chapter_id: X41
title: "ComfyUI Foundations"
layer: "Images"
status: "implemented"
purpose: "Build and execute ComfyUI workflows for image generation with FLUX and other models"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "20m"
inputs:
  - "Text prompt"
  - "Negative prompt"
  - "Model selection"
  - "Resolution settings"
outputs:
  - "Generated image (PNG)"
qc_gates:
  - "Image generated successfully"
  - "Image matches prompt description"
default_tools:
  primary: "ComfyUI + FLUX (flux1-schnell-q8.gguf)"
  fallback: "ZImage (Lumina2/AuraFlow)"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X41"
  run: "run_X41"
  score: "score_X41"
  retry: "retry_X41"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X41 — ComfyUI Foundations

## Chapter Card
**Chapter:** `X41 — ComfyUI Foundations`  
**Layer:** `Images`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Build and execute ComfyUI workflows for image generation with FLUX and other models.  
**Last Verified:** 2026-06-15

**Actual Implementation:**
- **File:** `app/backends/comfyui_image.py` (273 lines)
- **Endpoint:** `POST /api/image/generate`
- **ComfyUI URL:** `http://host.docker.internal:8188`
- **GPU Management:** Semaphore (max 2 concurrent tasks)

**Supported Models:**
| Model | Type | Notes |
|-------|------|-------|
| `flux1-schnell-q8.gguf` | FLUX | Default, fast |
| `z_image_turbo.safetensors` | ZImage | Lumina2/AuraFlow |
| `dreamshaper_8.safetensors` | SD 1.5 | Fast drafting |
| `sd_xl_base_1.0.safetensors` | SDXL | High quality |

**Quality Gates:**
- Gate 1: Image generated successfully
- Gate 2: Image matches prompt description

---

## 1) Quickstart (Golden Path)

### Goal
Generate an image from a text prompt using ComfyUI.

### When to run
- For image generation
- For thumbnail creation
- For visual content production

### Golden Path Steps
1) **Send image generation request**:
   ```bash
   curl -X POST http://localhost:5050/api/image/generate \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "A futuristic cityscape at sunset, cyberpunk style",
       "negative_prompt": "blurry, low quality, distorted",
       "model": "flux1-schnell-q8.gguf",
       "width": 1024,
       "height": 1024,
       "steps": 8
     }'
   ```
   Expected: Image URL returned

2) **Download image**:
   - Response contains `image_url` field
   - Download from: `http://localhost:5050/output/{filename}.png`

### Done looks like
- [ ] Request sent with valid prompt
- [ ] Image URL returned
- [ ] Image downloaded successfully
- [ ] Image matches prompt

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Prompt | `prompt` field | Text description of image |

### Optional Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Negative prompt | `negative_prompt` | Things to avoid |
| Model | `model` | Model to use (default: FLUX) |
| Width | `width` | Image width (default: 1024) |
| Height | `height` | Image height (default: 1024) |
| Steps | `steps` | Sampling steps (default: 8) |
| Seed | `seed` | Random seed |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Image URL | Response | URL to generated image |
| Job ID | Response | For tracking |

### Definition of Done (DoD)
Image generated + URL accessible + matches prompt.

---

## 3) Config & Standards

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `COMFYUI_URL` | `http://host.docker.internal:8188` | ComfyUI endpoint |
| `OUTPUT_DIR` | `/app/output` | Where to save images |

### Default Settings
- **Model:** flux1-schnell-q8.gguf
- **Resolution:** 1024x1024
- **Steps:** 8
- **CFG:** 1.0
- **Sampler:** euler
- **Scheduler:** normal

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool:** ComfyUI
  - **Workflow Engine:** JSON-based node graphs
  - **Endpoint:** `http://host.docker.internal:8188`
  - **Strengths:** Flexible, GPU-accelerated, many models
  - **Weaknesses:** Complex setup, VRAM-intensive

### Supported Models
| Model | VRAM | Speed | Quality |
|-------|------|-------|---------|
| FLUX schnell | ~8GB | Fast | Good |
| ZImage turbo | ~6GB | Fast | Good |
| Dreamshaper | ~4GB | Fast | Medium |
| SDXL Base | ~8GB | Medium | High |

---

## 5) Procedure (Operator Steps)

### Step 1 — Build Workflow JSON
- **Inputs:** Prompt, settings
- **Action:** Construct ComfyUI workflow nodes
- **Expected output:** Valid workflow JSON
- **Common failures:** Invalid node references
- **Fix:** Verify node IDs, check model names

### Step 2 — Submit to ComfyUI
- **Inputs:** Workflow JSON
- **Action:** POST to ComfyUI `/prompt` endpoint
- **Expected output:** Prompt ID for tracking
- **Common failures:** ComfyUI overloaded, model not loaded
- **Fix:** Check GPU memory, wait and retry

### Step 3 — Poll for Completion
- **Inputs:** Prompt ID
- **Action:** GET `/history/{prompt_id}`
- **Expected output:** Completion status + output nodes
- **Common failures:** Timeout, workflow error
- **Fix:** Check ComfyUI logs, verify workflow

### Step 4 — Retrieve Image
- **Inputs:** Output filename
- **Action:** GET `/view?filename={name}`
- **Expected output:** Image binary data
- **Common failures:** File not found
- **Fix:** Check output directory, verify filename

---

## 6) Agent Interface (Automation Hooks)

### API Endpoint
- `POST /api/image/generate`

### Request Format
```json
{
  "prompt": "Image description",
  "negative_prompt": "Things to avoid",
  "model": "flux1-schnell-q8.gguf",
  "width": 1024,
  "height": 1024,
  "steps": 8,
  "seed": 12345
}
```

### Response Format
```json
{
  "image_url": "/output/spark_{job_id}.png",
  "job_id": "img_abc12345"
}
```

---

## 7) Smoke Tests

### Smoke Test A — Minimal (fast)
- **Goal:** Prove image generation works
- **Input:** "A simple red circle on white background"
- **Steps:** Send request, verify image
- **Pass criteria:** Image generated, file size > 10KB
- **If fails:** Check ComfyUI running

### Smoke Test B — Standard (realistic)
- **Goal:** Test with complex prompt
- **Input:** Detailed scene description
- **Steps:** Generate, download, verify quality
- **Pass criteria:** Image matches prompt, good quality
- **If fails:** Adjust steps, check model

---

## 8) Troubleshooting

### Issue 1 — "ComfyUI connection refused"
- **Cause:** ComfyUI not running on host
- **Fix:** Start ComfyUI manually
- **Prevention:** Add to startup script

### Issue 2 — "GPU out of memory"
- **Cause:** Too many concurrent generations
- **Fix:** Wait for current task to finish
- **Prevention:** Semaphore limits concurrent tasks

### Issue 3 — "Model not found"
- **Cause:** Model file not downloaded
- **Fix:** Download model to ComfyUI models folder
- **Prevention:** Pre-download required models

### Issue 4 — "Image quality poor"
- **Cause:** Wrong model or low steps
- **Fix:** Try different model, increase steps
- **Prevention:** Test with sample prompts

---

## 9) Change Log

- 2026-06-15 — Initial implementation with actual codebase content
- 2025-12-24 — Original template created