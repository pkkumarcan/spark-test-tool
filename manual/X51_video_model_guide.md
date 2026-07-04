---
chapter_id: X51
title: "Video Model Selection Guide"
layer: "Video"
status: "implemented"
purpose: "Choose the right video model based on use case, quality, and GPU constraints"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "10m"
inputs:
  - "Use case requirements"
  - "GPU VRAM available"
outputs:
  - "Model recommendation"
  - "Settings configuration"
qc_gates:
  - "Model matches use case"
  - "VRAM requirements met"
default_tools:
  primary: "Decision matrix"
  fallback: "Trial and error"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X51"
  run: "run_X51"
  score: "score_X51"
  retry: "retry_X51"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X51 — Video Model Selection Guide

## Chapter Card
**Chapter:** `X51 — Video Model Selection Guide`  
**Layer:** `Video`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Choose the right video model based on use case, quality, and GPU constraints.  
**Last Verified:** 2026-06-15

**What Exists:**
- ✅ 6 video models supported in `comfyui_video.py`
- ✅ Model validation against `SUPPORTED_VIDEO_MODELS`
- ✅ Dynamic fallback selection based on VRAM capacity profiles mapped in code
- ✅ Target parameters (CFG, steps, frames) configured per model

---

## 1) Supported Models

### Video Models
| Model | Type | VRAM | Speed | Quality | Best For |
|-------|------|------|-------|---------|----------|
| `wan2.2_14b_q4.gguf` | Wan 2.2 MoE | ~12GB | Medium | High | General purpose |
| `ltx-2.3-22b-dev-Q4_K_M.gguf` | LTX | ~16GB | Fast | Good | Quick drafts |
| `cogvideox_5b_i2v_bf16.safetensors` | CogVideoX | ~12GB | Medium | High | Character animation |
| `allegro_v1_0_fp8.safetensors` | Allegro | ~8GB | Fast | Medium | Fast previews |
| `dreamshaper_8.safetensors` | AnimateDiff | ~4GB | Fast | Low | SD 1.5 style |
| `mochi_preview_fp8.safetensors` | Mochi | ~8GB | Medium | Medium | Experimental |

---

## 2) Selection Decision Tree

### By Use Case

**B-Roll / Nature Footage**
→ Use `wan2.2_14b_q4.gguf` (best quality) or `ltx-2.3-22b-dev-Q4_K_M.gguf` (faster)

**Character Animation**
→ Use `cogvideox_5b_i2v_bf16.safetensors` (best for people)

**Quick Previews**
→ Use `allegro_v1_0_fp8.safetensors` (fastest)

**Stylized / Anime**
→ Use `dreamshaper_8.safetensors` (AnimateDiff)

### By VRAM Available

| VRAM | Recommended Models |
|------|-------------------|
| 4GB | `dreamshaper_8.safetensors` only |
| 8GB | `allegro`, `mochi`, `dreamshaper` |
| 12GB | `wan2.2`, `cogvideox` |
| 16GB+ | All models including `ltx` |

### By Quality Priority

| Priority | Model | Notes |
|----------|-------|-------|
| Highest | `wan2.2_14b_q4.gguf` | Best overall quality |
| High | `cogvideox_5b` | Best for characters |
| Medium | `ltx-2.3-22b` | Good balance |
| Fast | `allegro_v1_0_fp8` | Quick iterations |

---

## 3) Settings by Model

### Wan 2.2 (Default)
```json
{
  "model": "wan2.2_14b_q4.gguf",
  "width": 768,
  "height": 448,
  "frames": 25,
  "steps": 20,
  "cfg": 6.0,
  "vae_tiling": true
}
```

### LTX
```json
{
  "model": "ltx-2.3-22b-dev-Q4_K_M.gguf",
  "width": 768,
  "height": 448,
  "frames": 25,
  "steps": 20,
  "cfg": 1.0
}
```

### CogVideoX
```json
{
  "model": "cogvideox_5b_i2v_bf16.safetensors",
  "width": 720,
  "height": 480,
  "frames": 49,
  "steps": 20,
  "cfg": 6.0
}
```

---

## 4) Resolution Guidelines

| Resolution | Use Case | Notes |
|------------|----------|-------|
| 768x448 | YouTube, general | Default, good balance |
| 512x512 | Square format | Social media |
| 480x320 | Quick previews | Fast generation |
| 1280x720 | HD | Requires more VRAM |

---

## 5) Troubleshooting

### Issue 1 — "Model not found"
- **Cause:** Model not in supported list
- **Fix:** Use one of the 6 supported models
- **Prevention:** Check `SUPPORTED_VIDEO_MODELS`

### Issue 2 — "GPU out of memory"
- **Cause:** Model too large for VRAM
- **Fix:** Use smaller model or reduce resolution
- **Prevention:** Check VRAM requirements

### Issue 3 — "Video quality poor"
- **Cause:** Wrong model for use case
- **Fix:** Try different model based on decision tree
- **Prevention:** Test with sample prompts

### Issue 4 — "Generation too slow"
- **Cause:** High-quality model on slow GPU
- **Fix:** Use faster model (allegro, dreamshaper)
- **Prevention:** Balance quality vs speed needs

---

## 6) Change Log

- 2026-06-15 — Documented model selection guidelines
- 2025-12-24 — Original template created