---
chapter_id: X64
title: "Thumbnail Finalization"
layer: "Assembly"
status: "implemented"
purpose: "Finalize and format video thumbnail variants with correct aspect ratios and safe margin validation"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "15m"
inputs:
  - "raw_thumbnail.png"
  - "config.thumbnail_settings"
outputs:
  - "thumbnail_1280x720.png"
qc_gates:
  - "safe_zone_check == PASSED"
  - "aspect_ratio == 16:9"
default_tools:
  primary: "Pillow"
  fallback: "FFmpeg"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X64"
  run: "run_X64"
  score: "score_X64"
  retry: "retry_X64"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X64 — Thumbnail Finalization

## Chapter Card
**Chapter:** `X64 — Thumbnail Finalization`  
**Layer:** `Assembly`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Crop, rescale, overlay brand assets, and test readability of final thumbnail images.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `/jobs/<job_id>/03_images/thumbnail_raw.png`
- `config.thumbnail_settings` (text layers and color configurations)

**Outputs (files):**
- `/jobs/<job_id>/publish/thumbnail_1280x720.png`

**Quality Gates (must pass):**
- `safe_zone_check == PASSED`: Critical elements (e.g. text) must not overlap with the bottom-right corner YouTube timestamp badge area (150px x 60px safe margin).
- `aspect_ratio == 16:9`: Resolution must match exactly 1280x720.

**Default tools:**
- `Pillow` (primary image manipulation tool)
- `FFmpeg` (fallback crop-scale pipeline)

**Automation hooks:**
- `validate_X64(job_id)`
- `run_X64(job_id, profile)`
- `score_X64(job_id)`
- `retry_X64(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Format raw square or portrait model generations into 1280x720 landscape thumbnails with high readability.

### When to run this chapter
- Immediately after raw thumbnail art generation (Chapter X44).
- Prior to compiling the final publish deliverable bundle.

### Default steps (golden path)
1) Load the raw generated thumbnail image into Pillow.
2) Apply a center crop to map the image to a `16:9` ratio, then resize to `1280x720`.
3) Check that the bottom-right region is clear of important text.
4) Save the final PNG file to the `/publish/` folder.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/publish/thumbnail_1280x720.png`
- [ ] QC passed: Image resolution and safe zone checks match.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X64]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Raw Image | `/jobs/<job_id>/03_images/thumbnail_raw.png` | Input image asset |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Final Thumbnail | `/jobs/<job_id>/publish/thumbnail_1280x720.png` | Target formatted thumbnail |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.thumbnail.width` | `1280` | Target thumbnail width |
| `config.thumbnail.height` | `720` | Target thumbnail height |

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Pillow
  - **Version/pin:** `>=10.0.0`
  - **Compute notes:** CPU execution (instantaneous)
  - **Strengths:** Precision cropping, clean bicubic resizing filters.

---

## 5) Procedure (Operator Steps)

### Step 1 — Center Crop and Resize
- **Inputs:** `thumbnail_raw.png`
- **Action:**
  - Execute a Python script that calculates target aspect boundaries and crops:
    ```python
    from PIL import Image
    img = Image.open("thumbnail_raw.png")
    w, h = img.size
    target_ratio = 16 / 9
    if w / h > target_ratio:
        new_w = int(h * target_ratio)
        crop_box = ((w - new_w) // 2, 0, (w + new_w) // 2, h)
    else:
        new_h = int(w / target_ratio)
        crop_box = (0, (h - new_h) // 2, w, (h + new_h) // 2)
    img_cropped = img.crop(crop_box).resize((1280, 720), Image.Resampling.LANCZOS)
    img_cropped.save("thumbnail_1280x720.png")
    ```
- **Expected output:** Properly proportioned 1280x720 landscape image.
- **Common failures:** Text gets cropped out on edges.
- **Fix:** Use a generative fill model or adjust crop offset coordinates.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X64(job_id)`: Checks image formats.
- `run_X64(job_id, profile)`: Crops and renders output.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Crop a 1000x1000 square image to 16:9.
- **Pass criteria:** Script completes and saves a 1280x720 image.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Size is exactly 1280x720.
- [ ] No visual squishing or scaling distortion.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `runtime_seconds`
- `crop_overlap_ratio`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Crucial Text Overlaps Badge Safe Area
- **Cause:** Graphic layout placed text layers in the bottom right corner.
- **Fix:** Move text overlays to the top-left or centered-left quadrants during canvas assembly.

---

## 11) Examples (Copy-paste)
- Example Python crop script:
  ```python
  from PIL import Image
  img = Image.open("source.png").resize((1280, 720))
  img.save("target_thumbnail.png")
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Artifacts** in `/jobs/<job_id>/publish/`
2. **Logs** in `/jobs/<job_id>/99_logs/X64/`
3. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Documented crop and aspect ratio guidelines.
