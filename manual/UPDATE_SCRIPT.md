# Manual Chapter Update Script

## Overview
This script helps update each chapter of the Spark AI Factory Manual systematically.

## Process Per Chapter

For each chapter (X01-X114), follow these steps:

### Step 1: Read Current Chapter
```bash
# Check if chapter file exists
ls manual/X##_*.md

# If exists, read it
cat manual/X##_*.md
```

### Step 2: Identify Status
Check the `status` field in YAML frontmatter:
- `implemented` → Update with actual code references
- `partial` → Document what exists vs what's missing
- `planned` → Keep template with future notes
- `reserved` → Mark as placeholder

### Step 3: If IMPLEMENTED — Read Relevant Code
```bash
# Find related endpoints
grep -n "X##" app/main.py

# Read backend implementation
cat app/backends/*.py | grep -A5 -B5 "def "

# Check docker-compose for service config
grep -A10 "service_name" docker-compose.yml
```

### Step 4: Update Chapter
Replace template content with actual implementation:
- Add actual API endpoints
- Add actual config keys
- Add actual tool/model names
- Add actual file references
- Update quality gates

### Step 5: Write Updated Chapter
```bash
# Write to manual/X##_name.md
```

### Step 6: Update INDEX.md
Change status in INDEX.md table.

---

## Chapter Priority Order

### High Priority (Implemented — Update First)
1. X04 — Local Platform Layer ✅ DONE
2. X11 — Research Workflow ✅ DONE
3. X12 — Knowledge Base / RAG
4. X21 — STT & Alignment (Whisper)
5. X22 — Voiceover TTS (F5-TTS)
6. X41 — ComfyUI Foundations
7. X42 — Image Generation Workflows
8. X52 — Text→Video Workflows
9. X53 — Image→Video Workflows

### Medium Priority (Partial — Document Gaps)
10. X01 — Orientation & Quickstart
11. X03 — Hardware / Storage / Network
12. X05 — Model Registry + Tool Index
13. X06 — Install & Version Pinning
14. X09 — Logging, Metrics & Observability
15. X10 — Reliability Basics
16. X33 — AI Music Generation
17. X45 — Keyframes & Storyboard Images
18. X51 — Video Model Selection Guide
19. X56 — Technical Enhancement
20. X62 — Audio/Video Sync & Mix-in
21. X92 — Security & Access Control

### Low Priority (Planned — Keep Template)
22-95. All planned chapters (keep template)

### Bonus Chapters (Update with Implementation Details)
96. X101-X114 — Already have content from earlier update

---

## Quick Reference: Implemented Chapters

| Chapter | Endpoint | File | Status |
|---------|----------|------|--------|
| X04 | `GET /health` | `app/main.py` | ✅ DONE |
| X11 | `POST /api/research/generate` | `app/backends/research_agent.py` | ✅ DONE |
| X12 | `POST /api/rag/ingest`, `POST /api/rag/query` | `app/backends/rag.py` | ✅ DONE |
| X21 | `POST /api/audio/transcribe` | `app/backends/whisper_stt.py` | ✅ DONE |
| X22 | `POST /api/audio/speak` | `app/backends/f5_tts.py` | ✅ DONE |
| X41 | `POST /api/image/generate` | `app/backends/comfyui_image.py` | ✅ DONE |
| X42 | `POST /api/image/generate` | `app/backends/comfyui_image.py` | ✅ DONE |
| X52 | `POST /api/video/generate` | `app/backends/comfyui_video.py` | ✅ DONE |
| X53 | `POST /api/video/generate` | `app/backends/comfyui_video.py` | ✅ DONE |

---

## Notes

- Each chapter file should be 200-500 lines
- Use the TEMPLATE.md format for consistency
- Always include actual code references (file:line)
- Update INDEX.md after each chapter is updated