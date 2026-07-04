---
chapter_id: X42
title: "Image Generation Workflows"
layer: "Images"
status: "implemented"
purpose: "Execute image generation workflows with multiple model support and resolution options"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "15m"
inputs:
  - "Text prompt"
  - "Model selection"
  - "Resolution settings"
outputs:
  - "Generated image (PNG)"
  - "Generation metadata"
qc_gates:
  - "Image generated within timeout"
  - "Resolution matches request"
default_tools:
  primary: "ComfyUI workflows"
  fallback: "Alternative models"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X42"
  run: "run_X42"
  score: "score_X42"
  retry: "retry_X42"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X42 — Image Generation Workflows

## Chapter Card
**Chapter:** `X42 — Image Generation Workflows`  
**Layer:** `Images`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Execute image generation workflows with multiple model support and resolution options.  
**Last Verified:** 2026-06-15

**Actual Implementation:**
- **File:** `app/backends/comfyui_image.py` (273 lines)
- **Endpoint:** `POST /api/image/generate`
- **Workflow Types:** FLUX, ZImage, SD, SDXL

**Quality Gates:**
- Gate 1: Image generated within timeout
- Gate 2: Resolution matches request

---

## 1) Quickstart (Golden Path)

### Goal
Generate images using different models and settings.

### When to run
- For production image generation
- For testing different models
- For batch image creation

### Golden Path Steps
1) **Generate with FLUX (default)**:
   ```bash
   curl -X POST http://localhost:5050/api/image/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Mountain landscape at dawn"}'
   ```

2) **Generate with ZImage**:
   ```bash
   curl -X POST http://localhost:5050/api/image/generate \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Abstract digital art",
       "model": "z_image_turbo.safetensors",
       "width": 720,
       "height": 1280
     }'
   ```

3) **Generate landscape format**:
   ```bash
   curl -X POST http://localhost:5050/api/image/generate \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Wide cinematic shot",
       "width": 1280,
       "height": 720
     }'
   ```

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Prompt | `prompt` | Text description |

### Optional Inputs
| Input | Path/Key | Default | Notes |
|-------|----------|---------|-------|
| Model | `model` | `flux1-schnell-q8.gguf` | Model to use |
| Width | `width` | 1024 | Image width |
| Height | `height` | 1024 | Image height |
| Steps | `steps` | 8 | Sampling steps |
| Seed | `seed` | random | Reproducibility |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Image URL | Response | Path to generated image |

---

## 3) Model Selection Guide

### FLUX Models
| Model | Use Case | VRAM | Speed |
|-------|----------|------|-------|
| `flux1-schnell-q8.gguf` | Fast generation | ~8GB | Fast |
| `flux1-dev-q8.gguf` | Higher quality | ~12GB | Medium |

### ZImage Models
| Model | Use Case | VRAM | Speed |
|-------|----------|------|-------|
| `z_image_turbo.safetensors` | Fast, good quality | ~6GB | Fast |

### SD/SDXL Models
| Model | Use Case | VRAM | Speed |
|-------|----------|------|-------|
| `dreamshaper_8.safetensors` | Creative, fast | ~4GB | Fast |
| `sd_xl_base_1.0.safetensors` | High quality | ~8GB | Medium |

---

## 4) Resolution Presets

| Name | Width | Height | Use Case |
|------|-------|--------|----------|
| Square | 1024 | 1024 | Social media, thumbnails |
| Landscape | 1280 | 720 | YouTube, presentations |
| Portrait | 720 | 1280 | Mobile, stories |
| Wide | 1536 | 640 | Cinematic, banners |

---

## 5) Troubleshooting

### Issue 1 — "Generation timeout"
- **Cause:** Complex prompt or busy GPU
- **Fix:** Reduce steps, use faster model
- **Prevention:** Monitor GPU usage

### Issue 2 — "Wrong resolution"
- **Cause:** Model doesn't support requested size
- **Fix:** Use compatible resolution
- **Prevention:** Check model documentation

### Issue 3 — "Image artifacts"
- **Cause:** Low steps or bad prompt
- **Fix:** Increase steps, refine prompt
- **Prevention:** Test with sample prompts

---

## 6) Change Log

- 2026-06-15 — Initial implementation with actual codebase content