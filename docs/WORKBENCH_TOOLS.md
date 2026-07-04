# Workbench Function Registry — docs/WORKBENCH_TOOLS.md

This document registers the strict input/output schemas and service dependencies for the manual workbench tools and system control endpoints available in the Spark media studio.

---

## 1. Text & Storytelling

### chat (`POST /api/text/chat`)
Generates long-form text or scripts using a local LLM with optional semantic memory.
- **Dependencies:** Ollama (default port `11434`), Qdrant (default port `6333` if RAG is enabled).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "model": { "type": "string", "description": "Ollama model identifier, e.g. qwen3.6:27b" },
      "messages": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "role": { "type": "string", "enum": ["user", "assistant", "system"] },
            "content": { "type": "string" }
          },
          "required": ["role", "content"]
        }
      },
      "system_prompt": { "type": "string" },
      "rag": { "type": "boolean", "default": false }
    },
    "required": ["messages"]
  }
  ```

### enhance (`POST /api/text/enhance`)
Expands raw user prompt drafts into descriptive cinematic prompts.
- **Dependencies:** Ollama (default port `11434`).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "prompt": { "type": "string", "description": "Raw input concept" },
      "model": { "type": "string", "default": "qwen3.6:27b" }
    },
    "required": ["prompt"]
  }
  ```

### list-models (`GET /api/text/models`)
Retrieves the list of locally pulled Ollama models.
- **JSON Output Sample:**
  ```json
  {
    "models": [
      {
        "name": "gemma4:12b-it-qat",
        "size": 8456201402
      }
    ]
  }
  ```

---

## 2. Diffusion Image & Video

### image (`POST /api/image/generate`)
Generates high-fidelity images using FLUX.1 or Stable Diffusion checkpoints.
- **Dependencies:** ComfyUI (default port `8188`), NVIDIA GPU (Semaphore lock).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "prompt": { "type": "string" },
      "negative_prompt": { "type": "string", "default": "blurry, low quality" },
      "steps": { "type": "integer", "minimum": 4, "maximum": 50, "default": 8 },
      "width": { "type": "integer", "default": 1024 },
      "height": { "type": "integer", "default": 1024 },
      "model": { "type": "string", "default": "flux1-schnell-q8.gguf" }
    },
    "required": ["prompt"]
  }
  ```

### video (`POST /api/video/generate`)
Queues video synthesis tasks as background processes. Returns a `job_id`.
- **Dependencies:** ComfyUI (default port `8188`), `job_store` queue database.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "prompt": { "type": "string" },
      "model": { "type": "string", "default": "ltx-2.3-22b-dev-Q4_K_M.gguf" },
      "mode": { "type": "string", "enum": ["t2v", "i2v"], "default": "t2v" },
      "width": { "type": "integer", "default": 768 },
      "height": { "type": "integer", "default": 448 },
      "frames": { "type": "integer", "default": 25 },
      "image": { "type": "string", "description": "Base64 data URL for image-to-video frames" }
    },
    "required": ["prompt"]
  }
  ```

### test-frame (`POST /api/video/test-frame`)
Generates a fast single frame to verify prompts and video layout composition before full queue submission.
- **Dependencies:** ComfyUI (default port `8188`).
- **JSON Input Schema:** Matches `video` schema.

---

## 3. Audio, Music & 3D

### speak (`POST /api/audio/speak`)
Synthesizes spoken audio voice from text input.
- **Dependencies:** F5-TTS / Kokoro (default port `8000`).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "text": { "type": "string" },
      "voice": { "type": "string", "default": "default" },
      "language": { "type": "string", "default": "en" }
    },
    "required": ["text"]
  }
  ```

### transcribe (`POST /api/audio/transcribe`)
Transcribes spoken files into text.
- **Dependencies:** Whisper ASR (default port `9000`).
- **Multipart Form Fields:**
  - `file` (Binary payload, required)
  - `language` (String, optional)

### music (`POST /api/music/generate`)
Composes audio tracks and songs. Returns a `job_id`.
- **Dependencies:** ComfyUI (default port `8188`).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "prompt": { "type": "string" },
      "model": { "type": "string", "default": "ace-step-1.5-base" },
      "lyrics": { "type": "string", "description": "Optional lyrics" }
    },
    "required": ["prompt"]
  }
  ```

### 3d (`POST /api/3d/generate`)
Converts descriptions into 3D meshes using Hunyuan3D. Returns a `job_id`.
- **Dependencies:** ComfyUI (default port `8188`).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "prompt": { "type": "string" },
      "mode": { "type": "string", "enum": ["shape_only", "shape_texture", "multiview"], "default": "shape_only" }
    },
    "required": ["prompt"]
  }
  ```

---

## 4. Extraction & Ingestion

### ocr (`POST /api/extract/ocr`)
Performs OCR extraction on uploaded image files.
- **Dependencies:** Ollama (default port `11434` running `llama3.2-vision:11b`).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "image_base64": { "type": "string", "description": "Base64 encoded image string" }
    },
    "required": ["image_base64"]
  }
  ```

### pdf (`POST /api/extract/pdf`)
Extracts text layout and parses content from a PDF file.
- **Multipart Form Fields:**
  - `file` (Binary PDF payload, required)
  - `ocr_all` (Boolean, default: `false`)
  - `auto_ingest` (Boolean, default: `false`)
  - `clean_spacing` (Boolean, default: `false`)
  - `fix_broken_sentences` (Boolean, default: `false`)
  - `preserve_paragraphs` (Boolean, default: `false`)
  - `chunk_size` (Integer, default: `1000`)
  - `chunk_overlap` (Integer, default: `100`)
  - `chunking_strategy` (String, default: `"sentence"`)

### link (`POST /api/extract/link`)
Crawls and extracts raw text from a target web URL.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "url": { "type": "string" },
      "auto_ingest": { "type": "boolean", "default": false },
      "clean_spacing": { "type": "boolean", "default": false },
      "fix_broken_sentences": { "type": "boolean", "default": false },
      "preserve_paragraphs": { "type": "boolean", "default": false },
      "chunk_size": { "type": "integer", "default": 1000 },
      "chunk_overlap": { "type": "integer", "default": 100 },
      "chunking_strategy": { "type": "string", "default": "sentence" }
    },
    "required": ["url"]
  }
  ```

### youtube (`POST /api/extract/youtube`)
Scrapes transcript/caption text files from YouTube videos.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "youtube_url": { "type": "string" }
    },
    "required": ["youtube_url"]
  }
  ```

---

## 5. RAG Storage Controls

### ingest (`POST /api/rag/ingest`)
Directly ingests a custom block of text context into Qdrant memory.
- **Dependencies:** Qdrant (default port `6333`).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "text": { "type": "string" },
      "metadata": { "type": "object", "default": {} },
      "chunk_size": { "type": "integer", "default": 1000 },
      "chunk_overlap": { "type": "integer", "default": 100 },
      "chunking_strategy": { "type": "string", "default": "sentence" }
    },
    "required": ["text"]
  }
  ```

### query (`POST /api/rag/query`)
Searches local memory matching the query terms.
- **Dependencies:** Qdrant (default port `6333`).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "query": { "type": "string" },
      "limit": { "type": "integer", "default": 3 },
      "search_mode": { "type": "string", "enum": ["semantic", "keyword"], "default": "semantic" }
    },
    "required": ["query"]
  }
  ```

### list-sources (`GET /api/rag/sources`)
Lists all ingested RAG source identifiers and files in Qdrant collections.
- **JSON Output Sample:**
  ```json
  {
    "sources": [
      "project_summary.pdf",
      "https://example.com/api-docs"
    ]
  }
  ```

### delete-source (`POST /api/rag/delete-source`)
Purges all chunks associated with a specific file source ID.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "source_id": { "type": "string" }
    },
    "required": ["source_id"]
  }
  ```

### clear-all (`POST /api/rag/clear-all`)
Deletes all points and drops Qdrant collection structures.
- **JSON Input Schema:** `{}`

---

## 6. Post-Processing & Smart Curation

### upscale (`POST /api/postprocess/upscale`)
Increases image resolution using Real-ESRGAN in ComfyUI. Returns `job_id`.
- **Dependencies:** ComfyUI (default port `8188`).
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "image_url": { "type": "string", "description": "Local output folder image path" },
      "scale_factor": { "type": "integer", "enum": [2, 4], "default": 2 }
    },
    "required": ["image_url"]
  }
  ```

### lipsync (`POST /api/postprocess/lipsync`)
Syncs a video's lips with a target audio track.
- **Multipart Form Fields:**
  - `video_file` (Binary payload, required)
  - `audio_file` (Binary payload, required)

### curate (`POST /api/curate/generate`)
Analyzes raw videos and generates compilation videos using face detection heuristics. Returns `job_id`.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "source_dir": { "type": "string", "default": "/app/media_ingest" },
      "strictness": { "type": "number", "default": 50 },
      "pacing": { "type": "number", "default": 3.0 }
    }
  }
  ```

---

## 7. Chained Workflows & Specialized Agents

### chain (`POST /api/chain/generate`)
Chains text, image, audio, and video models to create completed video stories. Returns `job_id`.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "topic": { "type": "string" },
      "scenes_count": { "type": "integer", "default": 3 }
    },
    "required": ["topic"]
  }
  ```

### research (`POST /api/research/generate`)
Launches deep web crawling and generates detailed Markdown reports. Returns `job_id`.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "topic": { "type": "string" },
      "depth": { "type": "integer", "default": 2 }
    },
    "required": ["topic"]
  }
  ```

### moa (`POST /api/moa/chat`)
Aggregates responses from Qwen, Llama, and Phi models using a Mixture of Agents structure.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "message": { "type": "string" },
      "history": { "type": "array", "default": [] }
    },
    "required": ["message"]
  }
  ```

### meme (`POST /api/meme/generate`)
Generates custom overlay memes. Returns `job_id`.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "topic": { "type": "string" },
      "template": { "type": "string", "default": "distracted_boyfriend" }
    },
    "required": ["topic"]
  }
  ```

### finance (`POST /api/gems/finance`)
Compiles market metrics for targeted ticker symbols.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "ticker": { "type": "string" }
    },
    "required": ["ticker"]
  }
  ```

### mcp (`POST /api/gems/mcp`)
Routes prompts dynamically through MCP servers.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "prompt": { "type": "string" }
    },
    "required": ["prompt"]
  }
  ```

### ingest-source (`POST /api/gems/ingest-source`)
Ingests a single source document specifically for contextual chat sessions.
- **Multipart Form Fields:**
  - `file` (Binary payload, required)

### chat-source (`POST /api/gems/chat-source`)
Performs contextual chat restricted to a single uploaded source file.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "message": { "type": "string" },
      "source_id": { "type": "string" }
    },
    "required": ["message", "source_id"]
  }
  ```

### voice-agent (`POST /api/gems/voice`)
Converts voice recording chunks to voice agent replies.
- **Multipart Form Fields:**
  - `file` (Binary speech WAV recording, required)

### generate-ui (`POST /api/gems/generate-ui`)
Synthesizes HTML/JS web application mockups on the fly.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "prompt": { "type": "string" }
    },
    "required": ["prompt"]
  }
  ```

### coding-agent (`POST /api/gems/coding-agent`)
Triggers stateful workspace coding iterations.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "task": { "type": "string" },
      "model": { "type": "string", "default": "qwen3:8b" },
      "max_iterations": { "type": "integer", "default": 5 }
    },
    "required": ["task"]
  }
  ```

---

## 8. Chat Orchestrator & Code Agent Controls

### chat-orchestration (`POST /api/orchestrator/chat`)
Primary entry point for the Chat-First UI. Orchestrates intent routing, vision checks, and returns action-based metadata.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "message": { "type": "string" },
      "context": { "type": "string", "default": "Default" },
      "history": { "type": "array", "default": [] },
      "model": { "type": "string", "description": "Orchestration LLM model" },
      "images": { "type": "array", "items": { "type": "string" }, "description": "Base64 image strings" },
      "active_contexts": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["message"]
  }
  ```

### code-stream (`GET /api/orchestrator/code/stream`)
Starts an SSE-based stream for stateful coding workspace sessions.
- **Query Parameters:**
  - `task` (String, required)
  - `model` (String, default: `"qwen3:8b"`)
  - `session_id` (String, optional)

### code-approve (`POST /api/orchestrator/code/approve`)
Approves a pending command or file write.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "session_id": { "type": "string" }
    },
    "required": ["session_id"]
  }
  ```

### code-reject (`POST /api/orchestrator/code/reject`)
Rejects a pending action with descriptive feedback.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "session_id": { "type": "string" },
      "feedback": { "type": "string", "default": "Rejected by user." }
    },
    "required": ["session_id"]
  }
  ```

### code-get-memory (`GET /api/orchestrator/code/memory`)
Retrieves the current content of the coding agent's `MEMORY.md` file.

### code-update-memory (`POST /api/orchestrator/code/memory`)
Overwrites the content of the coding agent's `MEMORY.md` file.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "memory": { "type": "string" }
    },
    "required": ["memory"]
  }
  ```

---

## 9. System & Assets Utilities

### gpu-status (`GET /api/gpu/status`)
Queries GPU resource utilization metrics from `nvidia-smi`.
- **JSON Output Sample:**
  ```json
  {
    "gpu_status": "GPU 0: NVIDIA RTX 3090 (24GB VRAM) - Temp: 58C, Utilization: 12%\nGPU 1: NVIDIA RTX 3060 (12GB VRAM) - Temp: 42C, Utilization: 0%"
  }
  ```

### list-assets (`GET /api/assets`)
Lists generated output assets sorted by creation time (descending).
- **JSON Output Sample:**
  ```json
  {
    "assets": [
      {
        "name": "video_gen_123.mp4",
        "url": "/output/video_gen_123.mp4",
        "type": "video"
      }
    ]
  }
  ```

### serve-asset (`GET /output/{filename}`)
Protected download/stream endpoint for output media files. Prevents directory-traversal.

### run-dify-workflow (`POST /api/dify/run-workflow`)
Triggers an external Dify workflow application.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workflow_id": { "type": "string" },
      "inputs": { "type": "object", "default": {} }
    },
    "required": ["workflow_id"]
  }
  ```
