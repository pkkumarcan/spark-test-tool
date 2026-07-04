# Batch Chapter Update Workflow

## Purpose
Automatically update all implemented chapter files with actual codebase content.

## Chapters to Update (Priority Order)

### Phase 1: High Priority (Implemented — Update First)
- [x] X21 — STT & Alignment (Whisper) ✅
- [x] X22 — Voiceover TTS (F5-TTS) ✅
- [x] X41 — ComfyUI Foundations ✅
- [x] X42 — Image Generation Workflows ✅
- [x] X52 — Text→Video Workflows ✅
- [x] X53 — Image→Video Workflows ✅

### Phase 2: Medium Priority (Partial — Document Gaps)
- [x] X01 — Orientation & Quickstart ✅
- [x] X03 — Hardware / Storage / Network ✅
- [x] X05 — Model Registry + Tool Index ✅
- [x] X06 — Install & Version Pinning ✅
- [x] X09 — Logging, Metrics & Observability ✅
- [x] X10 — Reliability Basics ✅
- [x] X33 — AI Music Generation ✅
- [x] X45 — Keyframes & Storyboard Images (covered in X41/X42)
- [x] X51 — Video Model Selection Guide ✅
- [x] X56 — Technical Enhancement ✅
- [x] X62 — Audio/Video Sync & Mix-in ✅
- [x] X92 — Security & Access Control ✅

### Phase 3: Low Priority (Planned — Create Templates)
- [x] X02 — Factory Contract ✅
- [x] X07 — Operations Runbook ✅
- [x] X08 — Smoke Tests & Benchmarking ✅
- [x] X13 — Master Story Script ✅
- [x] X14 — Voiceover Script Pack ✅
- [x] X15 — Visual Script Pack ✅
- [x] X16 — Music Script Pack ✅
- [x] X17 — Edit Blueprint (EDL-lite) ✅
- [x] X18 — Publishing Package Draft ✅
- [x] X19 — Blueprint QA & Compliance ✅
- [x] X20 — Production Blueprint Export ✅
- [x] X23-X26 — Audio Speech Reserved ✅
- [x] X31-X32, X34-X36 — Audio Music ✅
- [x] X43-X44, X46-X47 — Images ✅
- [x] X54-X55, X57 — Video ✅
- [x] X61, X63-X67 — Assembly ✅
- [x] X71-X75 — Publishing ✅
- [x] X81-X85 — Post-Publishing ✅
- [x] X91, X93-X100 — Governance ✅

### Phase 4: Bonus Chapters (Already Have Content)
- X101-X114 — Already updated in main manual

---

## Process Per Chapter

1. **Read chapter file** from `manual/X##_*.md`
2. **Read relevant code** from `app/backends/*.py` or `app/main.py`
3. **Update chapter** with actual:
   - API endpoints
   - Config keys
   - Tool/model names
   - File references
   - Quality gates
4. **Write updated chapter** back to file
5. **Update INDEX.md** status
6. **Update UPDATE_SCRIPT.md** checklist

---

## Code Mapping Reference

| Chapter | Primary Code File | Key Functions |
|---------|-------------------|---------------|
| X21 | `app/backends/whisper_stt.py` | `transcribe()` |
| X22 | `app/backends/f5_tts.py` | `speak()` |
| X41/X42 | `app/backends/comfyui_image.py` | `generate()` |
| X52/X53 | `app/backends/comfyui_video.py` | `generate()`, `generate_test_frame()` |
| X33 | `app/backends/comfyui_music.py` | `generate()` |
| X56 | `app/backends/postprocess.py` | `upscale()`, `lipsync()` |
| X92 | `app/backends/security_scanner.py` | `audit_command_string()`, `run_project_scan()` |

---

## Estimated Time Per Chapter

| Phase | Chapters | Time Each | Total |
|-------|----------|-----------|-------|
| Phase 1 | 6 | 10 min | ~1 hour |
| Phase 2 | 12 | 5 min | ~1 hour |
| Phase 3 | 74 | 1 min | ~1.5 hours |
| Phase 4 | 14 | 0 min | 0 (done) |
| **Total** | **106** | | **~3.5 hours** |

---

## Progress Tracking

```
Completed: 114/114 chapters (100%)
- Phase 1 (Implemented): 9 chapters ✅
- Phase 2 (Partial): 12 chapters ✅
- Phase 3 (Planned): 53 chapters ✅ (templates created)
- Phase 4 (Reserved): 27 chapters ✅ (templates created)
- Phase 5 (Bonus): 14 chapters ✅ (already have content)

All chapter files created in manual/ directory
```