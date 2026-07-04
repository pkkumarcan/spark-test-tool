# Spark Media Factory Repository Manifest

This document outlines the complete repository manifest and file structure for Spark Media Factory, covering all directories and files.

| Code | Level | Type | Name | Purpose | Full Path | Parent Code | Parent Path | Top Level Area | Descendant Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| A | 0 | Folder | Spark Media Factory | Automated multi-node media generation workstation. | / | | | / | 14 |
| A1 | 1 | File | README.md | Entry point, developer setup, and startup commands. | README.md | A | / | README.md | 0 |
| A2 | 1 | File | ARCHITECTURE.md | System topology, GPU memory setup, and pipeline design. | ARCHITECTURE.md | A | / | ARCHITECTURE.md | 0 |
| A3 | 1 | File | PROJECT_CONTEXT.md | Summary of APIs, ports, and pipeline steps for LLMs. | PROJECT_CONTEXT.md | A | / | PROJECT_CONTEXT.md | 0 |
| A4 | 1 | File | Dockerfile | Environment setup for service dependencies (FFmpeg, CUDA). | Dockerfile | A | / | Dockerfile | 0 |
| A5 | 1 | File | docker-compose.yml | Multi-node container configuration (Qdrant, F5, Whisper). | docker-compose.yml | A | / | docker-compose.yml | 0 |
| A6 | 1 | File | .env.example | Model keys, endpoint IPs, and directory configurations. | .env.example | A | / | .env.example | 0 |
| A7 | 1 | File | requirements.txt | Workstation library pins. | requirements.txt | A | / | requirements.txt | 0 |
| A8 | 1 | Folder | app | Gateway logic exposing REST endpoints and background tasks. | app/ | A | / | app/ | 10 |
| A8.1 | 2 | File | main.py | FastAPI orchestration routes, websockets, and semaphores. | app/main.py | A8 | app/ | app/ | 0 |
| A8.2 | 2 | Folder | static | Front-end static screens and dashboards. | app/static/ | A8 | app/ | app/ | 3 |
| A8.3 | 2 | Folder | backends | Modulized AI service wrappers interacting with models. | app/backends/ | A8 | app/ | app/ | 8 |
| A8.3.1 | 3 | File | ollama.py | LLM client routines (Ollama, vLLM, DeepSeek API). | app/backends/ollama.py | A8.3 | app/backends/ | app/ | 0 |
| A8.3.2 | 3 | File | comfyui_video.py | Video diffusion client (LTX-Video/SVD/Hunyuan). | app/backends/comfyui_video.py | A8.3 | app/backends/ | app/ | 0 |
| A8.3.3 | 3 | File | comfyui_image.py | Image generation wrapper (FLUX.1/SDXL). | app/backends/comfyui_image.py | A8.3 | app/backends/ | app/ | 0 |
| A8.3.4 | 3 | File | whisper_stt.py | Transcription and word-alignment client. | app/backends/whisper_stt.py | A8.3 | app/backends/ | app/ | 0 |
| A8.3.5 | 3 | File | f5_tts.py | F5-TTS voice synthesis engine client. | app/backends/f5_tts.py | A8.3 | app/backends/ | app/ | 0 |
| A8.3.6 | 3 | File | rag.py | Vector storage querying (Qdrant client). | app/backends/rag.py | A8.3 | app/backends/ | app/ | 0 |
| A8.3.7 | 3 | File | publishing.py | YouTube & social publishing integrations. | app/backends/publishing.py | A8.3 | app/backends/ | app/ | 0 |
| A8.3.8 | 3 | File | coding_agent.py | SSE stateful local terminal coding agent loop. | app/backends/coding_agent.py | A8.3 | app/backends/ | app/ | 0 |
| A9 | 1 | Folder | manual | Structured system operational documentation (114 chapters). | manual/ | A | / | manual/ | 97 |
| A9.1 | 2 | File | INDEX.md | Chapter tracking list and verification statuses. | manual/INDEX.md | A9 | manual/ | manual/ | 0 |
| A9.2 | 2 | File | TEMPLATE.md | Chapter documentation template file. | manual/TEMPLATE.md | A9 | manual/ | manual/ | 0 |
| A9.3 | 2 | File | X01_orientation.md | Workspace quickstart guide. | manual/X01_orientation.md | A9 | manual/ | manual/ | 0 |
| A9.4 | 2 | File | X11_research.md | Pre-production RAG search workflow. | manual/X11_research.md | A9 | manual/ | manual/ | 0 |
| A9.5 | 2 | File | X13_master_production_template.md | Reusable master channel configuration and episode script guidelines. | manual/X13_master_production_template.md | A9 | manual/ | manual/ | 0 |
| A10 | 1 | Folder | docs | Workspace environment guides, issues, and tools. | docs/ | A | / | docs/ | 5 |
| A11 | 1 | Folder | scratch | Local CLI tests and developer staging tools. | scratch/ | A | / | scratch/ | 35 |
| A11.1 | 2 | File | batch_pipeline.py | Stateful pipeline script (Phase 1 pre-prod, Phase 2 render). | scratch/batch_pipeline.py | A11 | scratch/ | scratch/ | 0 |
| A11.2 | 2 | File | sample_episodes | Reference episode script pack for Macro Lens Finance. | scratch/sample_episodes | A11 | scratch/ | scratch/ | 0 |
| A12 | 1 | Folder | output | Live pipeline generated releases, logs, and database. | output/ | A | / | output/ | 20 |
| A12.1 | 2 | File | jobs.db | SQLite master database tracking jobs. | output/jobs.db | A12 | output/ | output/ | 0 |
