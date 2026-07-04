---
chapter_id: X46
title: "Brand Assets"
layer: "Images"
status: "implemented"
purpose: "Generate logos, overlays, masks, and typography"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "1h"
inputs:
  - "config.brand_settings"
  - "job_manifest.json"
outputs:
  - "watermark_mask.png"
  - "overlay_layer.png"
qc_gates:
  - "file_existence == True"
  - "transparency_ratio >= 0.70"
default_tools:
  primary: "Pillow"
  fallback: "ComfyUI/FLUX.1-Schnell"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X46"
  run: "run_X46"
  score: "score_X46"
  retry: "retry_X46"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X46 — Brand Assets

## Chapter Card
**Chapter:** `X46 — Brand Assets`  
**Layer:** `Images`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Generate logos, overlays, masks, and typography layers for branding.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `config.brand_settings` (YAML/JSON keys defining colors, logo paths, watermarks)
- `job_manifest.json`

**Outputs (files):**
- `/jobs/<job_id>/03_images/brand_assets/watermark_mask.png`
- `/jobs/<job_id>/03_images/brand_assets/overlay_layer.png`

**Quality Gates (must pass):**
- `file_existence == True`: Both files must exist and be readable.
- `transparency_ratio >= 0.70`: Transparent overlays must have at least 70% transparent pixels.

**Default tools:**
- `Pillow` (primary drawing tool for standard shapes, text rendering, and compositing)
- `ComfyUI/FLUX.1-Schnell` (fallback for complex text generation and graphic assets)

**Automation hooks:**
- `validate_X46(job_id)`
- `run_X46(job_id, profile)`
- `score_X46(job_id)`
- `retry_X46(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Generate transparent PNG watermark and text overlay assets to be composited over video frames.

### When to run this chapter
- Immediately after the visual plan is finalized (Chapter X15).
- Before starting video assembly (Chapter X61) and final rendering.

### Default steps (golden path)
1) Read the brand configuration settings from `config.brand_settings`.
2) Initialize a transparent RGBA canvas in Python using Pillow.
3) Render typography layers (such as channel logo, video watermarks, or border masks) onto the canvas.
4) Save output layers directly to the brand assets folder for compositing.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/03_images/brand_assets/watermark_mask.png`
- [ ] Output exists: `/jobs/<job_id>/03_images/brand_assets/overlay_layer.png`
- [ ] QC passed: Transparency checks confirm layers are non-opaque.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X46]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Brand logo text | `config.brand_settings.watermark_text` | Text string to overlay |
| Font path | `/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf` | TrueType font for rendering |

### Optional Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Overlay PNG logo | `config.brand_settings.logo_file` | Absolute path to pre-rendered brand logo icon |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Watermark Mask | `/jobs/<job_id>/03_images/brand_assets/watermark_mask.png` | Transparent watermark mask |
| Title Overlay | `/jobs/<job_id>/03_images/brand_assets/overlay_layer.png` | Clean transparent typography overlay |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.brand_settings.watermark_text` | `"@SparkFactory"` | Default watermark text |
| `config.brand_settings.font_size` | `24` | Size of watermark text in pixels |
| `config.brand_settings.opacity` | `0.3` | Opacity level of watermark text (0.0 to 1.0) |

### Naming conventions (chapter-specific)
- Watermark files must use lowercase names: `watermark_mask.png`.
- Color values must be specified in hexadecimal (e.g. `#FFFFFF`) or RGBA tuples.

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Pillow (PIL Fork)
  - **Version/pin:** `>=10.0.0`
  - **Compute notes:** Runs on CPU (minimal RAM required)
  - **Strengths:** High-speed rendering, pixel-perfect placement, exact transparency control.
  - **Weaknesses:** Lacks advanced layout engines (manual line-wrapping required).

### Alternatives (approved)
- **ComfyUI / FLUX.1-Schnell** — Used when stylized generative logos or thematic vector-like brand assets are required.

---

## 5) Procedure (Operator Steps)

### Step 1 — Render Watermark Mask
- **Inputs:** `watermark_text`, `font_size`
- **Action:**
  - Create a new Pillow image: `Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))`
  - Load the TrueType font.
  - Compute text coordinates to place in the bottom-right corner with a 50px margin.
  - Draw text using `draw.text` with an opacity/fill value of `(255, 255, 255, 76)` (30% opacity).
- **Expected output:** A transparent 1080p image with the watermark text in the bottom right corner.
- **Common failures:** Font file missing.
- **Fix:** Fallback to standard system fonts or `ImageFont.load_default()`.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X46(job_id)`: Checks for brand asset paths in configuration.
- `run_X46(job_id, profile)`: Generates the PNG assets.
- `score_X46(job_id)`: Scores assets on transparency ratio.
- `retry_X46(job_id, strategy)`: Retries with default fonts if TrueType fonts fail.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Render a standard watermark mask on a default canvas.
- **Input:** Target text `"TEST"`
- **Steps:**
  ```python
  from PIL import Image, ImageDraw, ImageFont
  img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
  draw = ImageDraw.Draw(img)
  draw.text((10, 10), "TEST", fill=(255, 255, 255, 128))
  img.save("smoke_test_watermark.png")
  ```
- **Pass criteria:** File `smoke_test_watermark.png` exists and size > 0.
- **If fails:** Check write permissions in the local directory.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Transparent background exists.
- [ ] No clipping or overlap of text layers.
- [ ] Resolution matches target (1920x1080 or 1080x1920).

### Scoring rubric (1–10)
- **Quality:** 10 if text rendering is crisp and anti-aliased; 5 if text is pixelated.
- **Speed:** 10 if generated in <500ms.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `runtime_seconds`
- `artifact_size`
- `transparency_ratio`
- `resolution`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Missing Font Path
- **Cause:** Linux system doesn't have the Liberation or DejaVu fonts installed.
- **Fix:** Update python code to loop through a fallback list of paths or load PIL's built-in default font.

---

## 11) Examples (Copy-paste)
- Example Python script snippet to draw watermarks:
  ```python
  from PIL import Image, ImageDraw, ImageFont
  img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
  draw = ImageDraw.Draw(img)
  draw.text((1800, 1030), "@Spark", fill=(255, 255, 255, 77))
  img.save("watermark_mask.png")
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Artifacts** in `/jobs/<job_id>/03_images/brand_assets/`
2. **Logs** in `/jobs/<job_id>/99_logs/X46/`
3. **Manifest step entry** in `job_manifest.json`:
   - `pipeline_steps["X46"]`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Documented brand assets workflow using Pillow.
