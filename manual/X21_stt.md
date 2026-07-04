---
chapter_id: X21
title: "STT & Alignment (Whisper)"
layer: "Audio-Speech"
status: "implemented"
purpose: "Transcribe speech audio to text using faster-whisper with VAD filtering"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "10m"
inputs:
  - "Audio file (WAV/MP3)"
outputs:
  - "Transcription JSON with text"
qc_gates:
  - "Transcription completed without error"
  - "Text is intelligible"
default_tools:
  primary: "faster-whisper v1.6.0 (large-v3, float16)"
  fallback: "Manual transcription"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X21"
  run: "run_X21"
  score: "score_X21"
  retry: "retry_X21"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X21 — STT & Alignment (Whisper)

## Chapter Card
**Chapter:** `X21 — STT & Alignment (Whisper)`  
**Layer:** `Audio-Speech`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Transcribe speech audio to text using faster-whisper with VAD filtering.  
**Last Verified:** 2026-06-15

**Actual Implementation:**
- **File:** `app/backends/whisper_stt.py` (58 lines)
- **Endpoint:** `POST /api/audio/transcribe`
- **Model:** faster-whisper large-v3 (float16)
- **Container:** `onerahmet/openai-whisper-asr-webservice:v1.6.0-gpu`
- **Host Port:** 8010 (mapped from container port 9000)

**Quality Gates:**
- Gate 1: Transcription completed without error
- Gate 2: Text output is non-empty and intelligible

---

## 1) Quickstart (Golden Path)

### Goal
Transcribe an audio file to text using Whisper.

### When to run
- When processing voice recordings
- For subtitle/caption generation
- For voice-to-text workflows

### Golden Path Steps
1) **Upload audio file**:
   ```bash
   curl -X POST http://localhost:5050/api/audio/transcribe \
     -F "file=@audio.wav" \
     -F "language=en"
   ```
   Expected: JSON with transcription text

2) **Process response**:
   ```json
   {
     "text": "Transcribed text from the audio file...",
     "language": "en",
     "duration": 12.5
   }
   ```

### Done looks like
- [ ] Audio file uploaded successfully
- [ ] Transcription JSON returned
- [ ] Text is non-empty
- [ ] No errors in response

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Audio file | `file` field | WAV, MP3, or other audio formats |

### Optional Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Language | `language` field | Default: "en" (English) |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Transcription | Response JSON | Contains `text` field with transcribed content |

### Definition of Done (DoD)
Audio uploaded + transcription returned + text is non-empty.

---

## 3) Config & Standards

### Config keys used
| Key | Default | Meaning |
|-----|---------|---------|
| `WHISPER_URL` | `http://whisper-stt:9000` | Whisper service endpoint |

### Container Configuration
- **Image:** `onerahmet/openai-whisper-asr-webservice:v1.6.0-gpu`
- **Model:** `large-v3`
- **Engine:** `faster_whisper`
- **Quantization:** `float16`
- **Port mapping:** 8010 (host) → 9000 (container)

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool:** faster-whisper v1.6.0
  - **Model:** large-v3
  - **Precision:** float16
  - **VAD Filter:** Enabled
  - **Strengths:** High accuracy, fast inference, VAD support
  - **Weaknesses:** Requires GPU for real-time transcription

### Alternatives (approved)
- **OpenAI Whisper API** — Cloud-based, requires API key
- **Whisper.cpp** — CPU-only, slower but no GPU needed

---

## 5) Procedure (Operator Steps)

### Step 1 — Receive Audio Upload
- **Inputs:** Audio file from request
- **Action:** Save to temporary file
- **Expected output:** Temp file created
- **Common failures:** File too large, invalid format
- **Fix:** Check file size, verify format

### Step 2 — Send to Whisper
- **Inputs:** Temp file path
- **Action:** POST to Whisper `/asr` endpoint
- **Expected output:** JSON response with transcription
- **Common failures:** Whisper timeout, model loading
- **Fix:** Increase timeout, check GPU memory

### Step 3 — Parse Response
- **Inputs:** Whisper JSON response
- **Extract:** `text`, `language`, `duration`
- **Expected output:** Clean transcription text
- **Common failures:** Empty text, garbled output
- **Fix:** Check audio quality, try different language

### Step 4 — Cleanup
- **Inputs:** Temp file path
- **Action:** Delete temporary file
- **Expected output:** Temp file removed
- **Common failures:** File locked
- **Fix:** Force delete, ignore error

---

## 6) Agent Interface (Automation Hooks)

### API Endpoint
- `POST /api/audio/transcribe`

### Request Format
```
Content-Type: multipart/form-data

file: <audio binary>
language: en (optional)
```

### Response Format
```json
{
  "text": "Transcribed text...",
  "language": "en",
  "duration": 12.5
}
```

### Error Responses
- `400` — No file uploaded
- `502` — Whisper returned error
- `503` — Whisper container unreachable
- `500` — Transcription failed

---

## 7) Smoke Tests

### Smoke Test A — Minimal (fast)
- **Goal:** Prove transcription works
- **Input:** 5-second WAV file with clear speech
- **Steps:** Upload file, check response
- **Pass criteria:** Non-empty text returned
- **If fails:** Check Whisper container running

### Smoke Test B — Standard (realistic)
- **Goal:** Test with longer audio
- **Input:** 60-second MP3 with natural speech
- **Steps:** Upload file, verify accuracy
- **Pass criteria:** Transcription matches audio content
- **If fails:** Check GPU memory, try smaller file

---

## 8) Troubleshooting

### Issue 1 — "Whisper container unreachable"
- **Cause:** Whisper container not running
- **Fix:** `docker compose restart whisper-stt`
- **Prevention:** Check `docker compose ps`

### Issue 2 — "Transcription timeout"
- **Cause:** Audio file too long or GPU overloaded
- **Fix:** Split audio into smaller chunks
- **Prevention:** Monitor GPU usage

### Issue 3 — "Empty transcription"
- **Cause:** Audio has no speech or wrong language
- **Fix:** Check audio content, specify correct language
- **Prevention:** Verify audio before upload

### Issue 4 — "Invalid file format"
- **Cause:** Unsupported audio format
- **Fix:** Convert to WAV or MP3
- **Prevention:** Validate file type before upload

---

## 9) Change Log

- 2026-06-15 — Initial implementation with actual codebase content
- 2025-12-24 — Original template created