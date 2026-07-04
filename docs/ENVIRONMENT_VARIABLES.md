# System Environment Variables — docs/ENVIRONMENT_VARIABLES.md

This document serves as the reference guide for all environment variables used to configure the Spark Media Factory workstation. These variables are defined in the `.env` file (copied from `.env.example`).

---

## 1. Gateway & Server Settings

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `PORT` | `5050` | The port the FastAPI Gateway application listens on. |
| `HOST` | `0.0.0.0` | The interface bind address for FastAPI/Uvicorn. |

---

## 2. Service Integration Endpoints

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | The endpoint address for the Ollama LLM engine. |
| `COMFYUI_URL` | `http://host.docker.internal:8188` | The endpoint address for ComfyUI. |
| `WHISPER_URL` | `http://whisper-stt:9000` | Endpoint for the Whisper ASR speech-to-text service container. |
| `F5_TTS_URL` | `http://f5-tts:8000` | Endpoint for the F5-TTS voice synthesis container. |
| `QDRANT_URL` | `http://qdrant:6333` | Endpoint for the Qdrant Vector database container. |

---

## 3. Model Configuration Defaults

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `DEFAULT_LLM_MODEL` | `qwen3:8b` | The default text LLM model for standard text workbench generation. |
| `DEFAULT_VISION_MODEL` | `llama3.2-vision:11b` | The default vision LLM model for OCR/vision tasks. |
| `DEFAULT_EMBED_MODEL` | `nomic-embed-text:latest` | The model used to generate RAG vector embeddings. |
| `DEFAULT_IMAGE_MODEL` | `flux1-schnell-q8.gguf` | Default ComfyUI image checkpoint name. |
| `DEFAULT_VIDEO_MODEL` | `wan2.2_14b_q4.gguf` | Default ComfyUI video checkpoint name (e.g. LTX/Wan). |
| `ORCHESTRATOR_MODEL` | `gemma4:12b-it-qat` | The default orchestrator model for chat intent routing. |

---

## 4. Directories and Sandbox

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `OUTPUT_DIR` | `/app/output` | Gateway container path for saving generated output files. |
| `COMFYUI_OUTPUT_DIR`| `/comfyui-output` | Container volume mount directory mapping to ComfyUI output outputs. |
| `WORKSPACE_ROOT` | `/home/youruser/...` | The absolute path to the project root on the host, enforcing sandbox rules. |

---

## 5. Security & CORS Control

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `SPARK_API_KEY` | *(None)* | Optional API key token to restrict unauthorized endpoint access. |
| `ALLOWED_ORIGINS` | `http://localhost:5050` | Comma-separated list of browser origins permitted for CORS requests. |

---

## 6. Telemetry & Trace Logs

Configure these settings to trace and evaluate model generations on a local Langfuse server:

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `LANGFUSE_PUBLIC_KEY` | *(None)* | Public key credential for Langfuse connection. |
| `LANGFUSE_SECRET_KEY` | *(None)* | Secret key credential for Langfuse connection. |
| `LANGFUSE_HOST` | `http://host.docker.internal:3002` | The address of the Langfuse server dashboard. |

---

## 7. RAG Engine Configuration

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `RAG_ENGINE` | `local` | RAG search engine selector. Options: `local` (Qdrant), `ragflow`, or `anythingllm`. |

### RAGFlow Options (if `RAG_ENGINE=ragflow`)
- `RAGFLOW_URL`: Endpoint address for the RAGFlow API.
- `RAGFLOW_API_KEY`: API access token.
- `RAGFLOW_DATASET_ID`: Target RAGFlow collection dataset ID.

### AnythingLLM Options (if `RAG_ENGINE=anythingllm`)
- `ANYTHINGLLM_URL`: Endpoint address for the AnythingLLM API.
- `ANYTHINGLLM_API_KEY`: API access token.
- `ANYTHINGLLM_WORKSPACE`: Target workspace identifier.

---

## 8. Search APIs (Research Agent)

If no API keys are provided, the Research Agent automatically falls back to DuckDuckGo crawling.

- `TAVILY_API_KEY`: Tavily search engine API key.
- `SEARXNG_URL`: SearXNG search engine local endpoint (e.g. `http://host.docker.internal:8888`).
- `GOOGLE_API_KEY`: Google Custom Search API key.
- `GOOGLE_CSE_ID`: Google Custom Search Engine ID.

---

## 9. Yahoo Mail Organizer Subsystem

- `YAHOO_EMAIL`: Yahoo account email address.
- `YAHOO_APP_PASSWORD`: Yahoo App-specific Password generated under Yahoo Account Security.
- `YAHOO_IMAP_SERVER`: Yahoo IMAP server address (defaults to `export.imap.mail.yahoo.com`).

---

## 10. Dify Workflow Orchestrator

- `DIFY_API_URL`: Dify platform workspace server endpoint.
- `DIFY_API_KEY`: Access token for the Dif App workflow trigger.
