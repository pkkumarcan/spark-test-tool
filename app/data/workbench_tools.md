# Spark Media Workstation Node 1 — Workbench Tools Reference

This document describes all 20 manual workbench tools available in the studio, along with their parameters, settings, and guidelines for LLM tool selection.

---

### 1. Text & RAG (`text`)
* **Description:** Long-form text generation, scriptwriting, storytelling, and local semantic memory retrieval.
* **Settings:**
  * **Model Selection:**
    * `qwen3.6:27b` — Cinematic Prompt Architect (Expanded visual concepts)
    * `qwen3:14b` — Balanced Creative Writer
    * `qwen3:8b` — Standard Fast Writer
    * `qwen3:4b` — Instant Router / Draft Generator
    * `llama3.2-vision:11b` — Image-to-Text describer
    * `llama3.2:latest` — 3B light model
    * `phi3:latest` — 3.8B lightweight model
  * **System Instruction:** Overrides assistant persona (default: "You are a cinematic prompt architect").
  * **Local Memory Search (RAG):** Enable/disable retrieval from Qdrant vector database.
  * **Topic/Prompt:** Text input area.

### 2. FLUX Image (`image`)
* **Description:** High-fidelity image generation using FLUX.1.
* **Settings:**
  * **Model:** `flux1-schnell-q8.gguf`
  * **Resolution:** Square (1024x1024), Landscape (1280x720), or Portrait (720x1280).
  * **Steps:** 4 to 50 (default: 25).
  * **Negative Prompt:** Text input to filter features (default: "blurry, low quality, distorted").

### 3. Non-FLUX Image / Fast Image (`fastimage`)
* **Description:** Fast image generation for rapid drafting.
* **Settings:**
  * **Models:**
    * `dreamshaper_8.safetensors` (SD 1.5 - Fast)
    * `sd_xl_base_1.0.safetensors` (SDXL 1.0 Base)
    * `juggernaut_xl_lightning.safetensors` (4-Step Lightning)
    * `z_image_turbo.safetensors`
  * **Resolution:** Square (1024x1024), Landscape (1280x720), Portrait (720x1280), or Classic Square (512x512).
  * **Steps:** 1 to 25 (default: 4).
  * **Negative Prompt:** Text filters.

### 4. Video Generation (`video`)
* **Description:** Synthesizes short animations or video clips from text or images.
* **Settings:**
  * **Models:**
    * `ltx-2.3-22b-dev-Q4_K_M.gguf` — Recommended standard model
    * `cogvideox_5b_i2v_bf16.safetensors` — Good for image-to-video
    * `allegro_v1_0_fp8.safetensors` — Fast FP8 model
    * `dreamshaper_8.safetensors` — AnimateDiff (SD 1.5)
    * `wan2.2_14b_q4.gguf` — Wan 2.2 MoE model
  * **Modes:** Text-to-Video (`t2v`), Image-to-Video (`i2v`), or Interpolation (between first and last frame).
  * **Dimensions:** Width & Height (256 to 1280, default: 768x448).
  * **Frames:** 9 to 97 (default: 25).

### 5. Audio & Speech (`audio`)
* **Description:** Audio transcription and text-to-speech.
* **Settings:**
  * **Whisper Transcription (STT):** Takes audio file, outputs text. Supports English or Auto-detect.
  * **Speech Generation (Kokoro/F5):** Synthesizes text to spoken voice.
  * **Voices:** English, Spanish, Portuguese, German.

### 6. Music Generation (`music`)
* **Description:** Composes background tracks or full vocal songs.
* **Settings:**
  * **Models:**
    * `ace-step-1.5-base` — Song Draft
    * `heartmula-ace-step` — ACE-Step XL Turbo + HeartMuLa 3B (Full Vocal Song)
  * **Prompt:** Genre/Style description.
  * **Lyrics:** Optional text input.

### 7. 3D Asset Generation (`3d`)
* **Description:** Converts descriptions into 3D meshes using Hunyuan3D.
* **Settings:**
  * **Mode:** Shape Only (Fast Geometry), Shape + Texture (Full PBR Asset), or Multi-View (Cinematic Hero).
  * **Prompt:** Description of object.

### 8. Ingest & OCR (`extract`)
* **Description:** Ingests external files into local Qdrant memory.
* **Settings:**
  * **Vision OCR:** Extracts text from uploaded images using Qwen 2.5 VL.
  * **PDF Extractor:** Extracts PDF text with optional OCR.
  * **Web Link Extractor:** Scrapes webpage URL.
  * **Raw Text Input:** Directly input custom notes.
  * **Chunking Options:** Size (default: 1000), overlap (default: 100), strategy (NLTK Sentence vs Fixed Character).
  * **Auto-Ingest Toggle:** If enabled, directly indexes text into Qdrant vector database.

### 9. Post-Process (`postprocess`)
* **Description:** Upscales images or synchronizes video lip movement.
* **Settings:**
  * **Upscaler:** Real-ESRGAN (2x or 4x scale factor).
  * **Lip Sync:** LatentSync (Aligns mouth movements in video with a target audio track).

### 10. Smart Curation (`curate`)
* **Description:** Generates curated compilation clips from raw video folders.
* **Settings:** Source directory, strictness (1-100), and pacing cuts (seconds).

### 11. AI Storyteller (`story`)
* **Description:** Chains text, image, audio, and video generation to create multi-scene video stories.

### 12. Deep Research (`research`)
* **Description:** Autonomously formulates search queries, crawls the web, reads pages, and writes markdown reports.

### 13. MoA Chat (`moa`)
* **Description:** Combines outputs of multiple LLM agents (Qwen, Llama, Phi) using a Mixture of Agents aggregator.

### 14. Meme Factory (`meme`)
* **Description:** Custom template meme generator with text overlays.

### 15. Memory DB (`rag-memory`)
* **Description:** Inspects local Qdrant memory collections, showing chunk metrics and allowing item deletion.

### 16. Finance Team (`finance`)
* **Description:** Multi-agent financial research, compiling market metrics and ticker info.

### 17. MCP Agent (`mcp` / `spark-coder`)
* **Description:** Local file execution and tools using Model Context Protocol. Replaced/extended by the Spark Coder Workspace.

### 18. Chat with Source (`chat-source`)
* **Description:** Q&A restricted to the context of a single uploaded source file.

### 19. Voice Agent (`voice-agent`)
* **Description:** Voice-to-voice conversational LLM agent.

### 20. Generative UI (`gen-ui`)
* **Description:** Generates and renders dynamic HTML/JS components inside the user's viewport.
