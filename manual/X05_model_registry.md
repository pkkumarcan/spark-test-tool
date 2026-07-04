---
chapter_id: X05
title: "Model Registry + Tool Index"
layer: "Foundation"
status: "implemented"
purpose: "Maintain a single source of truth for all models, tools, and assets"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "20m"
inputs:
  - "Installed tools and models"
outputs:
  - "Model registry"
  - "Tool index"
  - "Asset library"
qc_gates:
  - "All models documented with versions"
  - "All tools have input/output schemas"
  - "No duplicate entries"
default_tools:
  primary: "Markdown documentation"
  fallback: "JSON registry"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X05"
  run: "run_X05"
  score: "score_X05"
  retry: "retry_X05"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X05 — Model Registry + Tool Index

## Chapter Card
**Chapter:** `X05 — Model Registry + Tool Index`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Maintain a single source of truth for all models, tools, and assets.  
**Last Verified:** 2026-06-15

**What Exists:**
- ✅ `app/data/workbench_tools.md` — 20 tool descriptions
- ✅ Model names in `.env.example`
- ✅ Dynamic `/api/text/models` endpoint queries local Ollama/vLLM models
- ✅ Docker image version tags mapped in docker compose configs

---

## 1) Tool Registry (20 Tools)

### Audio Tools
| Tool | Endpoint | Description |
|------|----------|-------------|
| `audio/transcribe` | POST | Whisper STT |
| `audio/speak` | POST | F5-TTS synthesis |

### Image Tools
| Tool | Endpoint | Description |
|------|----------|-------------|
| `image/generate` | POST | FLUX/SD image generation |
| `video/generate` | POST | Video generation (t2v/i2v) |
| `video/test-frame` | POST | Preview frame generation |
| `3d/generate` | POST | 3D asset generation |

### Music Tools
| Tool | Endpoint | Description |
|------|----------|-------------|
| `music/generate` | POST | ACE-Step music generation |

### Extraction Tools
| Tool | Endpoint | Description |
|------|----------|-------------|
| `extract/ocr` | POST | Image OCR |
| `extract/pdf` | POST | PDF text extraction |
| `extract/link` | POST | Web page scraping |
| `extract/youtube` | POST | YouTube transcript |

### RAG Tools
| Tool | Endpoint | Description |
|------|----------|-------------|
| `rag/ingest` | POST | Document ingestion |
| `rag/query` | POST | Semantic search |
| `rag/sources` | GET | List sources |
| `rag/delete-source` | POST | Delete source |
| `rag/clear-all` | POST | Clear knowledge base |

### Post-Processing Tools
| Tool | Endpoint | Description |
|------|----------|-------------|
| `postprocess/upscale` | POST | Image upscaling |
| `postprocess/lipsync` | POST | Lip sync |

### Research Tools
| Tool | Endpoint | Description |
|------|----------|-------------|
| `research/generate` | POST | Web research |

### Agent Tools
| Tool | Endpoint | Description |
|------|----------|-------------|
| `orchestrator/chat` | POST | Chat orchestrator |
| `gems/coding-agent` | POST | Coding agent |

---

## 2) Model Registry

### LLM Models (Ollama)
| Model | Size | Purpose | VRAM |
|-------|------|---------|------|
| `gemma4:12b-it-qat` | 12B | Orchestrator routing | ~8GB |
| `qwen3:14b` | 14B | Coding, research | ~10GB |
| `qwen3:8b` | 8B | Fast inference | ~6GB |
| `qwen3:4b` | 4B | Router, drafts | ~3GB |
| `llama3.2-vision:11b` | 11B | Vision tasks | ~8GB |
| `nomic-embed-text:v1.5` | 137M | Embeddings | ~1GB |

### Image Models (ComfyUI)
| Model | Type | Purpose | VRAM |
|-------|------|---------|------|
| `flux1-schnell-q8.gguf` | FLUX | Fast image gen | ~8GB |
| `dreamshaper_8.safetensors` | SD 1.5 | Creative drafts | ~4GB |
| `sd_xl_base_1.0.safetensors` | SDXL | High quality | ~8GB |
| `z_image_turbo.safetensors` | ZImage | Fast, good quality | ~6GB |

### Video Models (ComfyUI)
| Model | Type | Purpose | VRAM |
|-------|------|---------|------|
| `wan2.2_14b_q4.gguf` | Wan 2.2 | High quality video | ~12GB |
| `ltx-2.3-22b-dev-Q4_K_M.gguf` | LTX | Fast video | ~16GB |
| `cogvideox_5b_i2v_bf16.safetensors` | CogVideoX | i2v animation | ~12GB |
| `allegro_v1_0_fp8.safetensors` | Allegro | Fast FP8 | ~8GB |

### Audio Models
| Model | Service | Purpose |
|-------|---------|---------|
| `large-v3` | Whisper | Speech-to-text |
| F5-TTS | F5-TTS | Text-to-speech |
| `ace-step-1.5-base` | ComfyUI | Music generation |

---

## 3) Docker Images

| Service | Image | Version |
|---------|-------|---------|
| Gateway | Custom build | `Dockerfile` |
| Whisper | `onerahmet/openai-whisper-asr-webservice` | `v1.6.0-gpu` |
| F5-TTS | `climatologist/f5-tts` | `latest` |
| Qdrant | `qdrant/qdrant` | `latest` |

---

## 4) Troubleshooting

### Issue 1 — "Model not found"
- **Cause:** Model not pulled in Ollama
- **Fix:** `ollama pull <model_name>`
- **Prevention:** Pre-pull models after install

### Issue 2 — "Model too large for GPU"
- **Cause:** Insufficient VRAM
- **Fix:** Use smaller model variant
- **Prevention:** Check VRAM requirements

### Issue 3 — "Tool endpoint not working"
- **Cause:** Backend module not loaded
- **Fix:** Check `main.py` imports
- **Prevention:** Verify all backends imported

---

## 5) Change Log

- 2026-06-15 — Documented actual model and tool registry
- 2025-12-24 — Original template created