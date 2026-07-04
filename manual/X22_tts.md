---
chapter_id: X22
title: "Voiceover TTS (F5-TTS)"
layer: "Audio-Speech"
status: "implemented"
purpose: "Generate speech audio from text using F5-TTS with multiple voice options"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "10m"
inputs:
  - "Text to speak"
  - "Voice selection"
  - "Speed setting"
outputs:
  - "WAV audio file"
qc_gates:
  - "Audio file generated successfully"
  - "Audio is playable and intelligible"
default_tools:
  primary: "F5-TTS (climatologist/f5-tts:latest)"
  fallback: "Manual voice recording"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X22"
  run: "run_X22"
  score: "score_X22"
  retry: "retry_X22"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X22 — Voiceover TTS (F5-TTS)

## Chapter Card
**Chapter:** `X22 — Voiceover TTS (F5-TTS)`  
**Layer:** `Audio-Speech`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Generate speech audio from text using F5-TTS with multiple voice options.  
**Last Verified:** 2026-06-15

**Actual Implementation:**
- **File:** `app/backends/f5_tts.py` (76 lines)
- **Endpoint:** `POST /api/audio/speak`
- **Container:** `climatologist/f5-tts:latest`
- **Host Port:** 8020 (mapped from container port 8000)
- **Languages:** en, es, pt, de

**Quality Gates:**
- Gate 1: Audio file generated successfully
- Gate 2: Audio is playable and intelligible

---

## 1) Quickstart (Golden Path)

### Goal
Generate speech audio from text.

### When to run
- For voiceover generation
- For text-to-speech workflows
- For accessibility features

### Golden Path Steps
1) **Send text for synthesis**:
   ```bash
   curl -X POST http://localhost:5050/api/audio/speak \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Hello, welcome to the Spark Media Factory.",
       "voice": "en",
       "speed": 1.0
     }'
   ```
   Expected: WAV audio file returned

2) **Save audio file**:
   - Response is binary WAV data
   - Save to file: `output.wav`

### Done looks like
- [ ] Request sent with valid text
- [ ] WAV audio file received
- [ ] Audio plays correctly
- [ ] No errors in response

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Text | `text` field | Text to synthesize (required) |

### Optional Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Voice | `voice` field | Language/accent (default: "default") |
| Speed | `speed` field | Playback speed (default: 1.0) |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Audio file | Response binary | WAV format, playable |

### Definition of Done (DoD)
Text provided + audio generated + file playable.

---

## 3) Config & Standards

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `F5_TTS_URL` | `http://f5-tts:8000` | F5-TTS service endpoint |
| `OUTPUT_DIR` | `/app/output` | Where to save generated files |

### Container Configuration
- **Image:** `climatologist/f5-tts:latest`
- **Port mapping:** 8020 (host) → 8000 (container)
- **GPU:** Required for synthesis

### Voice Options
| Voice Code | Language | Notes |
|------------|----------|-------|
| `en` | English | Default |
| `es` | Spanish | |
| `pt` | Portuguese | |
| `de` | German | |

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool:** F5-TTS
  - **Version:** Latest (Docker image)
  - **Endpoint:** `http://f5-tts:8000`
  - **Strengths:** High-quality neural TTS, multiple languages
  - **Weaknesses:** Requires GPU, limited language support

### Alternatives (approved)
- **Coqui XTTS** — Voice cloning capable
- **Edge TTS** — Microsoft cloud TTS, requires internet

---

## 5) Procedure (Operator Steps)

### Step 1 — Validate Input
- **Inputs:** Request JSON body
- **Action:** Check `text` field exists and non-empty
- **Expected output:** Valid text string
- **Common failures:** Empty text, missing field
- **Fix:** Return 400 error

### Step 2 — Call F5-TTS
- **Inputs:** Text, voice, speed
- **Action:** POST to F5-TTS `/synthesize` endpoint
- **Expected output:** Audio content (binary)
- **Common failures:** F5-TTS timeout, model loading
- **Fix:** Check GPU memory, increase timeout

### Step 3 — Save Audio File
- **Inputs:** Audio binary content
- **Action:** Save to `{OUTPUT_DIR}/{job_id}.wav`
- **Expected output:** WAV file on disk
- **Common failures:** Disk full, permissions
- **Fix:** Check disk space, verify permissions

### Step 4 — Return Response
- **Inputs:** Saved file path
- **Action:** Return `FileResponse` with audio
- **Expected output:** Binary WAV data to client
- **Common failures:** File not found
- **Fix:** Verify file exists before returning

---

## 6) Agent Interface (Automation Hooks)

### API Endpoint
- `POST /api/audio/speak`

### Request Format
```json
{
  "text": "Text to synthesize",
  "voice": "en",
  "speed": 1.0
}
```

### Response Format
- **Content-Type:** `audio/wav`
- **Body:** Binary WAV data

### Error Responses
- `400` — Text is required
- `502` — F5-TTS returned error
- `503` — F5-TTS container unreachable
- `500` — TTS generation failed

---

## 7) Smoke Tests

### Smoke Test A — Minimal (fast)
- **Goal:** Prove TTS works
- **Input:** "Hello world"
- **Steps:** Send request, save audio
- **Pass criteria:** WAV file generated, plays correctly
- **If fails:** Check F5-TTS container running

### Smoke Test B — Standard (realistic)
- **Goal:** Test longer text
- **Input:** Paragraph of text (100+ words)
- **Steps:** Send request, verify quality
- **Pass criteria:** Audio natural-sounding, no artifacts
- **If fails:** Check GPU memory, adjust speed

---

## 8) Troubleshooting

### Issue 1 — "F5-TTS container unreachable"
- **Cause:** F5-TTS container not running
- **Fix:** `docker compose restart f5-tts`
- **Prevention:** Check `docker compose ps`

### Issue 2 — "TTS generation timeout"
- **Cause:** Text too long or GPU overloaded
- **Fix:** Split text into smaller chunks
- **Prevention:** Monitor GPU usage

### Issue 3 — "Audio quality poor"
- **Cause:** Wrong voice selection or speed setting
- **Fix:** Try different voice, adjust speed
- **Prevention:** Test with sample text first

### Issue 4 — "Invalid file format"
- **Cause:** F5-TTS returned unexpected response
- **Fix:** Check F5-TTS logs, verify endpoint
- **Prevention:** Validate response content-type

---

## 9) Change Log

- 2026-06-15 — Initial implementation with actual codebase content
- 2025-12-24 — Original template created