# Spark Media Factory: Project Context Manifest

This manifest provides a comprehensive system summary, layout overview, and implementation state for external AI models performing system-wide evaluations or reviews.

---

## 1. Project Purpose & Core Domain
The **Spark Media Factory** is an automated, multi-node media generation and publishing workstation. It takes niche topic instructions and automates the creation of long-form and short-form video releases.

Recently, the linear pipeline was refactored into a **Split-Phase Pre-Production & Production Queue**:
1. **Phase 1 (Pre-Production):** Performs research, trend matching via RAG, selected topic scoring, title variants suggestion, and script synthesis. Once Step B (Compliance Check) completes, the pipeline pauses, saving state as `pending_approval`.
2. **Phase 2 (Production Rendering):** Resumes only upon explicit human approval. Spawns tasks to generate audio (F5-TTS), visual blocks (ComfyUI), upscale visual blocks to 4K 60fps (Topaz/FFmpeg), stitch assets (FFmpeg), conduct multimodal QC, and publish to YouTube/TikTok.

---

## 2. Directory Layout & Key File Map

```text
spark-test-tool/
├── app/
│   ├── main.py                    # FastAPI gateway exposing REST endpoints and background loops
│   ├── static/
│   │   ├── pipeline_dashboard.html # Split-queue pipeline control dashboard
│   │   └── ...                    # Static pages for Chat-First workspace and Mail organizers
│   └── backends/                  # Modulized AI service wrappers
│       ├── job_store.py           # SQLite WAL + memory job queue
│       ├── ollama.py              # LLM routes (supports Ollama, vLLM, DeepSeek API)
│       ├── comfyui_video.py       # ComfyUI LTX/SVD video generation
│       ├── comfyui_image.py       # ComfyUI FLUX image generation
│       ├── whisper_stt.py         # Whisper ASR transcription
│       ├── f5_tts.py              # F5 Voice synthesis
│       ├── rag.py                 # Multi-engine vector search (Qdrant/RAGFlow)
│       ├── publishing.py          # YouTube & social publishing integrations
│       └── coding_agent.py        # SSE stateful local terminal coding agent loop
├── scratch/
│   ├── batch_pipeline.py          # Stateful CLI runner executing Phase 1 and Phase 2 loops
│   └── ...
├── docs/                          # Sub-system documentation
├── docker-compose.yml             # Local services orchestration (F5, Whisper, Qdrant, Gateway)
└── ARCHITECTURE.md                # Multi-node topology and hardware description
```

---

## 3. Technology Stack & Runtime Configuration

### Services & Port Assignments
- **Gateway Server:** FastAPI/Uvicorn served on Port `5050`
- **LLM/Ollama:** Host service on Port `11434`
- **ComfyUI Diffusion:** Host service on Port `8188`
- **Whisper STT:** Container service on Port `9000` (mapped on host to `8010`)
- **F5-TTS voiceover:** Container service on Port `8000` (mapped on host to `8020`)
- **Qdrant Vector Database:** Container service on Port `6333`

### Concurrency & VRAM Management
To prevent VRAM Out-of-Memory (OOM) failures under heavy model loading (FLUX + LTX-Video + TTS), the gateway implements an `asyncio.Semaphore(2)` in `app/main.py` to gate concurrent GPU-bound tasks.

### Sandbox & Security Constraints
- **File Access:** Verified via `is_safe_path()` checks restricting operations to the project workspace.
- **Command Runs:** Filtered via `ALLOWED_COMMANDS` list to block dangerous shell injections (like curl piping to bash or raw deletes).
- **Audit Chain:** Code modifications to dependency configurations are scanned for vulnerabilities via static checks.

---

## 4. Pipeline State Flow

### Step Timeline
- **Step A:** Topic & Idea Generation (Phase 1)
- **Step B:** Scripting & Compliance QA (Phase 1) -> *Gate: Awaiting approval*
- **Step C:** Voiceover & Audio Mastering (Phase 2)
- **Step D:** Visual Keyframe Storyboarding (Phase 2)
- **Step E:** Topaz 4K 60fps Upscaling (Phase 2)
- **Step F:** Subtitle Burn & Timeline Stitch (Phase 2)
- **Step G:** Long-Form YouTube Publishing (Phase 2)
- **Step H:** Short-Form Platforms Clips (Phase 2)
- **Step QC:** Multimodal Sync & Content QC (Phase 2)

### State Files
State is stored in JSON files per job under `output/jobs/{job_id}/`:
- `state.json`: Tracks progress and status for steps A-QC. Status transitions: `running` -> `pending_approval` -> `running` -> `completed` / `failed`.
- `a3_selected_topic.json`: Generated in Step A.
- `b1_master_script.json`: Generated in Step B.
- `b3_voiceover_pack.json`: Voice script chunk mappings.
- `job_manifest.json`: Final completion details.
