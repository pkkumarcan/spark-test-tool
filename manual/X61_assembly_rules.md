---
chapter_id: X61
title: "Assembly Rules"
layer: "Assembly"
status: "implemented"
purpose: "Build timeline structure by stitching scenes and matching audio lengths"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "1h"
inputs:
  - "scene_images"
  - "scene_audio"
outputs:
  - "stitched_story.mp4"
qc_gates:
  - "scenes_match_count == True"
  - "audio_video_aligned == True"
default_tools:
  primary: "FFmpeg"
  fallback: "Python/Subprocess"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X61"
  run: "run_X61"
  score: "score_X61"
  retry: "retry_X61"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X61 — Assembly Rules

## Chapter Card
**Chapter:** `X61 — Assembly Rules`  
**Layer:** `Assembly`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Compile and stitch individual audio-image pairs into unified video sequences with correct dimensions.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `/jobs/<job_id>/temp_<job_id>/image_<index>.png`
- `/jobs/<job_id>/temp_<job_id>/audio_<index>.wav`

**Outputs (files):**
- `/jobs/<job_id>/<job_id>.mp4`

**Quality Gates (must pass):**
- `scenes_match_count == True`: Final video must contain all planned scenes from the script.
- `audio_video_aligned == True`: No audio overhang or black frame gaps at scene transitions.

**Default tools:**
- `FFmpeg` (primary timeline stitcher and encoder)
- `Python/Subprocess` (automation manager executing system commands)

**Automation hooks:**
- `validate_X61(job_id)`
- `run_X61(job_id, profile)`
- `score_X61(job_id)`
- `retry_X61(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Assemble single scene media pairs (image + voiceover) into individual scene videos, then concatenate them to form the master timeline.

### When to run this chapter
- Immediately after scene visual elements and TTS segments are generated.
- Before running subtitles or post-processing polishing.

### Default steps (golden path)
1) For each scene, run an FFmpeg loop command using the image as a still input and matching the exact duration of the scene's audio file.
2) Output intermediate scene MP4s at `1024x1024` or the target aspect ratio.
3) Write a text file `concat.txt` containing list paths to all scene MP4s.
4) Invoke the FFmpeg concat demuxer with `-c copy` to merge the scenes into the final cut.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/<job_id>.mp4`
- [ ] QC passed: Concat completed without re-encoding errors or audio sync issues.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X61]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Images List | `/jobs/<job_id>/temp_*/image_*.png` | Input still frames |
| Audio Files | `/jobs/<job_id>/temp_*/audio_*.wav` | Matching scene voiceovers |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Master Cut | `/jobs/<job_id>/<job_id>.mp4` | Combined raw cut |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.assembly.resolution` | `"1024:1024"` | Resolution width and height mapping |
| `config.assembly.vcodec` | `"libx264"` | Video encoder profile |
| `config.assembly.acodec` | `"aac"` | Audio encoder profile |

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** FFmpeg
  - **Version/pin:** `>=6.0`
  - **Compute notes:** Runs on CPU (multiple threads supported)
  - **Strengths:** High reliability, no generation drift, exact timeline control.

---

## 5) Procedure (Operator Steps)

### Step 1 — Render Scene Clips
- **Inputs:** `image_0.png`, `audio_0.wav`
- **Action:**
  - Execute command:
    ```bash
    ffmpeg -y -loop 1 -framerate 25 -i image_0.png -i audio_0.wav \
      -c:v libx264 -tune stillimage -c:a aac -b:a 192k -ar 44100 -ac 2 \
      -pix_fmt yuv420p -vf scale=1024:1024 -shortest scene_0.mp4
    ```
- **Expected output:** A clean MP4 file named `scene_0.mp4` matching `audio_0.wav`'s length.
- **Common failures:** Subprocess returns non-zero code if input formats are mismatched.
- **Fix:** Pre-convert audio sample rates to 44.1kHz.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X61(job_id)`: Verifies asset lists.
- `run_X61(job_id, profile)`: Runs the compile process.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Stitch a 1x1 test image and blank wav source.
- **Pass criteria:** FFmpeg finishes successfully.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Total runtime matches the sum of all audio lengths.
- [ ] No audio popping or frame drop artifacts.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `runtime_seconds`
- `ffmpeg_return_code`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Concat Audio Sync Shift
- **Cause:** Concatenating clips with different audio sample rates or channel counts.
- **Fix:** Enforce strict `-ar 44100` and `-ac 2` constraints during the initial scene rendering step.

---

## 11) Examples (Copy-paste)
- Example Python segment compiler:
  ```python
  import subprocess
  cmd = [
      "ffmpeg", "-y", "-loop", "1", "-framerate", "25", "-i", img_path,
      "-i", audio_path, "-c:v", "libx264", "-c:a", "aac",
      "-vf", "scale=1024:1024", "-shortest", output_path
  ]
  subprocess.run(cmd, check=True)
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X61/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Documented FFmpeg timeline compilation rules.
