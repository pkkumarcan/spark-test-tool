---
chapter_id: X03
title: "Hardware / Storage / Network"
layer: "Foundation"
status: "implemented"
purpose: "Document hardware requirements, storage layout, and network configuration"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "15m"
inputs:
  - "System inventory"
outputs:
  - "Hardware profile"
  - "Storage layout"
  - "Network configuration"
qc_gates:
  - "GPU detected and accessible"
  - "Storage paths valid"
  - "Network ports available"
default_tools:
  primary: "nvidia-smi, docker"
  fallback: "Manual inspection"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X03"
  run: "run_X03"
  score: "score_X03"
  retry: "retry_X03"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X03 — Hardware / Storage / Network

## Chapter Card
**Chapter:** `X03 — Hardware / Storage / Network`  
**Layer:** `Foundation`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Document hardware requirements, storage layout, and network configuration.  
**Last Verified:** 2026-06-15

**What Exists:**
- ✅ GPU status endpoint (`GET /api/gpu/status`)
- ✅ Active network hardware & topology map: [spark_master_rag_manifest.md](file:///home/pkkumar/AGGY/spark-test-tool/app/data/spark_master_rag_manifest.md)
- ✅ Storage tier backup procedures
- ✅ Strict LAN port binding rules

---

## 1) Hardware Requirements

### Minimum Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 16GB | 32GB+ |
| GPU VRAM | 8GB | 12GB+ (RTX 3060+) |
| Storage | 50GB free | 100GB+ SSD |
| OS | Ubuntu 20.04 | Ubuntu 22.04 LTS |

### GPU Requirements
- **NVIDIA GPU** with CUDA support
- **NVIDIA Container Toolkit** installed for Docker GPU passthrough
- **Recommended:** RTX 3060 12GB or better

### Check GPU Status
```bash
# From host
nvidia-smi

# From API
curl http://localhost:5050/api/gpu/status
```

---

## 2) Storage Layout

### Directory Structure
```
spark-test-tool/
├── output/                 # Generated assets (mapped to /app/output)
├── qdrant_storage/         # Qdrant database (mapped to /qdrant/storage)
├── cache/                  # Model cache
│   └── whisper/            # Whisper model cache
├── app/static/             # Frontend files (mapped to /app/app/static)
├── app/data/               # RAG runtime context files
│   └── spark_master_rag_manifest.md # Active network hardware & topology map
└── .env                    # Configuration (never commit)
```

### Docker Volume Mounts
| Host Path | Container Path | Purpose |
|-----------|----------------|---------|
| `./output` | `/app/output` | Generated assets |
| `./qdrant_storage` | `/qdrant/storage` | Vector database |
| `./cache/whisper` | `/root/.cache` | Whisper models |
| `./app/static` | `/app/app/static` | Frontend files |
| ComfyUI output | `/comfyui-output` | ComfyUI generated files |

### Storage Requirements
| Data | Size | Growth Rate |
|------|------|-------------|
| Qdrant DB | ~100MB | ~1MB per 1000 documents |
| Generated assets | Variable | Per generation |
| Model cache | ~20GB | One-time download |
| Logs | ~10MB/day | Daily rotation |

---

## 3) Network Configuration

### Port Mapping
| Service | Host Port | Container Port | Protocol |
|---------|-----------|----------------|----------|
| Gateway | 5050 | 5050 | HTTP |
| Whisper | 8010 | 9000 | HTTP |
| F5-TTS | 8020 | 8000 | HTTP |
| Qdrant | 6333 | 6333 | HTTP |
| Qdrant gRPC | 6334 | 6334 | gRPC |
| Topaz AI (Node B) | 5060 | 5060 | HTTP |

### Network Interfaces
- **Gateway:** Binds to `0.0.0.0:5050` (configurable via `HOST` env var)
- **Internal services:** Use Docker internal DNS (e.g., `http://whisper-stt:9000`)
- **Host services:** Use `host.docker.internal` (e.g., Ollama, ComfyUI)

### CORS Configuration
```bash
# Default: localhost only
ALLOWED_ORIGINS=http://localhost:5050,http://127.0.0.1:5050

# For LAN access (add your LAN IP)
ALLOWED_ORIGINS=http://localhost:5050,http://192.168.1.100:5050
```

---

## 4) Environment Variables

### Core Configuration
| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | 5050 | Gateway port |
| `HOST` | 0.0.0.0 | Gateway bind address |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Ollama endpoint |
| `COMFYUI_URL` | `http://host.docker.internal:8188` | ComfyUI endpoint |
| `WHISPER_URL` | `http://whisper-stt:9000` | Whisper endpoint |
| `F5_TTS_URL` | `http://f5-tts:8000` | F5-TTS endpoint |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant endpoint |
| `OUTPUT_DIR` | `/app/output` | Output directory |

### Model Configuration
| Variable | Default | Purpose |
|----------|---------|---------|
| `DEFAULT_LLM_MODEL` | `qwen3:8b` | Default LLM model |
| `DEFAULT_VISION_MODEL` | `llama3.2-vision:11b` | Vision model |
| `DEFAULT_EMBED_MODEL` | `nomic-embed-text:latest` | Embedding model |
| `DEFAULT_IMAGE_MODEL` | `flux1-schnell-q8.gguf` | Image model |
| `DEFAULT_VIDEO_MODEL` | `wan2.2_14b_q4.gguf` | Video model |

---

## 5) Troubleshooting

### Issue 1 — "GPU not detected"
- **Cause:** NVIDIA drivers or Container Toolkit missing
- **Fix:** Install nvidia-driver-535, nvidia-docker2
- **Prevention:** Run `nvidia-smi` before Docker setup

### Issue 2 — "Port already in use"
- **Cause:** Another service on same port
- **Fix:** Change port in `.env` or stop conflicting service
- **Prevention:** Check ports before starting

### Issue 3 — "Docker permission denied"
- **Cause:** User not in docker group
- **Fix:** `sudo usermod -aG docker $USER`
- **Prevention:** Configure Docker permissions during install

### Issue 4 — "Storage full"
- **Cause:** Generated assets filling disk
- **Fix:** Clean old assets, expand storage
- **Prevention:** Monitor disk usage

---

## 6) Change Log

- 2026-06-15 — Documented actual hardware/storage/network configuration
- 2025-12-24 — Original template created