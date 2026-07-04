---
chapter_id: X62
title: "Audio/Video Sync & Mix-in"
layer: "Assembly"
status: "implemented"
purpose: "Synchronize audio with video and mix multiple audio tracks with sidechain compression ducking"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "20m"
inputs:
  - "video_cut.mp4"
  - "voiceover_file.wav"
  - "bg_music.mp3"
outputs:
  - "mixed_master.mp4"
qc_gates:
  - "lipsync_coherence_match == True"
  - "voiceover_perceptible == True"
default_tools:
  primary: "ffmpeg"
  fallback: "LatentSync"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X62"
  run: "run_X62"
  score: "score_X62"
  retry: "retry_X62"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X62 — Audio/Video Sync & Mix-in

## Chapter Card
**Chapter:** `X62 — Audio/Video Sync & Mix-in`  
**Layer:** `Assembly`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Sync voiceover files to video frames and mix music layers with automated volume compression (ducking).  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `/jobs/<job_id>/<job_id>.mp4` (raw video assembly)
- `/jobs/<job_id>/02_audio/voiceover/`
- `/jobs/<job_id>/02_audio/bg_music.mp3`

**Outputs (files):**
- `/jobs/<job_id>/master_mix.mp4`

**Quality Gates (must pass):**
- `lipsync_coherence_match == True`: Verbal voice timing matches speaker lip movements.
- `voiceover_perceptible == True`: Voiceover audio signal is clearly audible over background music.

**Default tools:**
- `ffmpeg` (primary audio mixer and sidechain compressor)
- `LatentSync` (fallback machine-learning based lipsync synthesizer, currently stubbed)

**Automation hooks:**
- `validate_X62(job_id)`
- `run_X62(job_id, profile)`
- `score_X62(job_id)`
- `retry_X62(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Overlay voiceover track and background music onto a stitched video, automatically lowering the background music volume whenever voiceover is active (ducking).

### When to run this chapter
- Instantly after assembling the raw cuts (Chapter X61).
- Prior to adding burnt-in open captions or subtitles (Chapter X63).

### Default steps (golden path)
1) Load the voiceover channel and background music channel.
2) Apply FFmpeg `sidechaincompress` or `amix` filters to mix the audio streams.
3) Use the `postprocess/lipsync` API route for model-based face/audio sync alignments.
4) Write the final mixed stream directly to `master_mix.mp4`.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/master_mix.mp4`
- [ ] QC passed: Voiceover volume is normalized; background music ducks to 20% volume during narration.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X62]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Assembly Cut | `/jobs/<job_id>/<job_id>.mp4` | Main video layer |
| Voiceover Track | `/jobs/<job_id>/temp_*/audio_*.wav` | Narration voice files |
| Music Track | `/jobs/<job_id>/02_audio/bg_music.mp3` | Soundtrack audio |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Synced Mixed Video | `/jobs/<job_id>/master_mix.mp4` | Video with completed audio track |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `config.mix.music_volume` | `0.15` | Default volume scale for background music |
| `config.mix.duck_ratio` | `2.5` | Ratio multiplier for sidechain compressor |

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** FFmpeg Audio Filter Complex
  - **Version/pin:** `>=6.0`
  - **Compute notes:** CPU execution (minimal overhead)
  - **Strengths:** Exact, reliable sidechain compression mapping without generation latency.

---

## 5) Procedure (Operator Steps)

### Step 1 — Apply Sidechain Compression
- **Inputs:** `master_cut.mp4`, `voiceover.wav`, `bg_music.mp3`
- **Action:**
  - Execute FFmpeg complex filter:
    ```bash
    ffmpeg -y -i master_cut.mp4 -i voiceover.wav -i bg_music.mp3 \
      -filter_complex "[2:a]sidechaincompress=threshold=0.01:ratio=2.5:attack=15:release=250[ducked];[1:a][ducked]amix=inputs=2:duration=first" \
      -c:v copy -map 0:v -map 1:a master_mix.mp4
    ```
- **Expected output:** Unified file with compressed soundtrack levels.
- **Common failures:** Length mismatch between music and video.
- **Fix:** Constrain mixed output to the shortest stream duration.

---

## 6) Agent Interface (Automation Hooks)

### Functions (stable)
- `validate_X62(job_id)`: Checks audio file structures.
- `run_X62(job_id, profile)`: Fires lipsync/mix tasks.

---

## 7) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Run sidechain compressor on two 2-second sine waves.
- **Pass criteria:** Command completes without errors.

---

## 8) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] No audio clipping or distortion.
- [ ] Soundtrack ducks when narration begins.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `runtime_seconds`
- `peak_db`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — Music Overpowers Narration
- **Cause:** Sidechain compressor threshold is set too high.
- **Fix:** Lower the compression threshold parameter (e.g. to `0.005`) in the FFmpeg filter string.

---

## 11) Examples (Copy-paste)
- Example python automation function:
  ```python
  import subprocess
  def mix_audio(video, voice, music, out):
      cmd = [
          "ffmpeg", "-y", "-i", video, "-i", voice, "-i", music,
          "-filter_complex", "[2:a]sidechaincompress=threshold=0.01:ratio=2.5[ducked];[1:a][ducked]amix=inputs=2",
          "-c:v", "copy", out
      ]
      subprocess.run(cmd, check=True)
  ```

---

## 12) Standard Chapter Artifacts (Required for Consistency)

This chapter must produce or update:
1. **Logs** in `/jobs/<job_id>/99_logs/X62/`
2. **Manifest step entry** in `job_manifest.json`

---

## 13) Change Log (Chapter Local)

- 2026-06-15 — Wrote sidechain compress and amix automation rules.