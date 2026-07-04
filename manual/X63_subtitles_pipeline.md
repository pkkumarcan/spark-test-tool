---
chapter_id: X63
title: "Subtitles Pipeline"
layer: "Assembly"
status: "implemented"
purpose: "Transcribe audio to SRT/ASS captions and burn them in using FFmpeg"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - "mixed_master.mp4"
outputs:
  - "subtitled_output.mp4"
qc_gates:
  - "transcription_accuracy >= 0.90"
  - "subtitle_burn_in == True"
default_tools:
  primary: "Whisper STT Server"
  fallback: "FFmpeg subtitles filter"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X63"
  run: "run_X63"
  score: "score_X63"
  retry: "retry_X63"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X63 — Subtitles Pipeline

## Chapter Card
**Chapter:** `X63 — Subtitles Pipeline`  
**Layer:** `Assembly`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Transcribe video soundtracks to SRT format and burn styled captions directly into the video stream.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `/jobs/<job_id>/master_mix.mp4`

**Outputs (files):**
- `/jobs/<job_id>/subtitled_final.mp4`
- `/jobs/<job_id>/99_logs/X63/transcription.srt`

**Quality Gates (must pass):**
- `transcription_accuracy >= 0.90`: Word-error rate (WER) must be below 10%.
- `subtitle_burn_in == True`: Video frames must contain visually burnt-in text tracks.

**Default tools:**
- `Whisper STT Server` (primary speech-to-text transcriber)
- `FFmpeg subtitles filter` (primary text burn-in compositor)

**Automation hooks:**
- `validate_X63(job_id)`
- `run_X63(job_id, profile)`
- `score_X63(job_id)`
- `retry_X63(job_id, strategy)`

**Smoke test time:** `~10 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Convert voiceover audio tracks to timed text, format them into SRT, and burn them into the target MP4 file.

### When to run this chapter
- Immediately after mixing the soundtrack elements (Chapter X62).
- Before final deliverables packaging and export.

### Default steps (golden path)
1) Extract the voiceover track from the video file.
2) Send the audio file to the `/asr` endpoint of the Whisper server to generate timed segments.
3) Format the JSON segment boundaries into standard SRT timestamps.
4) Run the FFmpeg subtitles filter command to burn the caption track into the output frames.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/subtitled_final.mp4`
- [ ] Output exists: `/jobs/<job_id>/99_logs/X63/transcription.srt`
- [ ] QC passed: Audio is matched within +/- 100ms by caption appearances.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X63]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Synced Master Video | `/jobs/<job_id>/master_mix.mp4` | Combined video input |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Burned-in Subtitles | `/jobs/<job_id>/subtitled_final.mp4` | Final subtitled output file |
| Timed Captions | `/jobs/<job_id>/99_logs/X63/transcription.srt` | Subtitles data file |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.subtitles.language` | `"en"` | Language code for Whisper STT model |
| `config.subtitles.font_style` | `"DejaVuSans-Bold"` | Burn-in caption font face |

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Whisper STT Container
  - **Version/pin:** Faster-Whisper Large-v3
  - **Compute notes:** Runs on GPU (requires 4GB VRAM) or CPU (medium speed)
  - **Strengths:** Accurate timestamps and automatic noise filtration.

---

## 5) Procedure (Operator Steps)

### Step 1 — Parse Whisper JSON to SRT
- **Inputs:** Whisper JSON output.
- **Action:**
  - Map each speech segment dictionary to SRT syntax:
    ```python
    def to_srt_timestamp(sec):
        hrs, mins = int(sec // 3600), int((sec % 3600) // 60)
        secs, ms = int(sec % 60), int(round((sec % 1) * 1000))
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"
    ```
- **Expected output:** Valid SRT file content.
- **Common failures:** Subtitles text wraps poorly or clips screen edges.
- **Fix:** Restrict each caption segment to a maximum of 35 characters.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X63(job_id)`: Verifies video codec profiles.
- `run_X63(job_id, profile)`: Dispatches Whisper tasks and burns text.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Transcribe a 2-second voice file.
- **Pass criteria:** SRT file is written.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] Captions contain no overlapping timestamps.
- [ ] Subtitle placement is centered in the lower third of the frame.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `runtime_seconds`
- `wer_score`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Subtitle Timing Lag
- **Cause:** Whisper Voice Activity Detector (VAD) filter is cutting off leading vowels.
- **Fix:** Set `"vad_filter": "false"` in the ASR request parameters to capture raw voice start points.

---

## 11) Examples (Copy-paste)
- Example FFmpeg subtitle burn command:
  ```bash
  ffmpeg -y -i master_mix.mp4 -vf "subtitles=transcription.srt:force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3'" subtitled_final.mp4
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X63/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Documented Whisper transcribe and FFmpeg burn-in routines.
