"""
Spark Orchestrator — Intent detection and routing for the Chat-First UI.
Optimized for Gemma 4 architecture (direct JSON instruction following,
no chain-of-thought, no <think> tokens).

Routing strategy:
  1. Send user message + history to Gemma4 with a strict JSON routing prompt
  2. Parse the routing JSON to get {action, reply, params}
  3. For text/chat → execute Ollama directly and return full response
  4. For image/video/audio/music/3d/research → return intent + params
     (frontend renders an "action card" with a Generate button, and
      an "Edit in Workbench" pass-through button)
"""

import os
import json
import logging
import httpx

logger = logging.getLogger("spark.orchestrator")

# ─── Gemma 4 Routing System Prompt ────────────────────────────────────────────
# Gemma 4 (12B QAT) works best with:
#   - Explicit JSON schema with examples
#   - No chain-of-thought preamble ("Do not explain, just output JSON")
#   - Short, imperative instructions
#   - Single clear constraint: output ONLY the JSON object

ROUTING_SYSTEM_PROMPT = """You are Spark Orchestrator, an AI dispatcher for a creative media production studio.

TASK: Analyze the user's message and output ONLY a valid JSON routing object. No preamble, no explanation.

JSON FORMAT (strict — output nothing else):
{
  "action": "<action_type>",
  "reply": "<concise friendly message shown to user, max 2 sentences>",
  "params": { <action-specific fields> }
}

ACTION TYPES:
1. "chat" — General conversation or questions. No media generation.
   params: {}

2. "image" — User wants to generate an image/photo/artwork/illustration.
   params: {
     "prompt": "<detailed visual description extracted from user message>",
     "model": "flux1-schnell-q8.gguf",
     "width": 1024, "height": 1024, "steps": 8,
     "negative_prompt": "blurry, low quality, distorted"
   }

3. "video" — User wants to generate a video/animation/clip.
   params: {
     "prompt": "<motion description>",
     "model": "ltx-2.3-22b-dev-Q4_K_M.gguf",
     "width": 768, "height": 448, "frames": 25
   }

4. "audio" — User wants text-to-speech / voice synthesis.
   params: {
     "text": "<exact text to speak>",
     "voice": "en", "speed": 1.0
   }

5. "music" — User wants AI music / soundtrack generation.
   params: {
     "prompt": "<genre and style description>",
     "model": "ace-step-1.5-base",
     "lyrics": ""
   }

6. "3d" — User wants a 3D asset/model.
   params: {
     "prompt": "<object description>",
     "mode": "shape"
   }

7. "research" — User wants deep research on a topic.
   params: {
     "topic": "<research topic>",
     "depth": "standard"
   }

8. "text" — User wants long-form text: script, story, article, prompt expansion.
   params: {
     "prompt": "<full user request>",
     "model": "qwen3:14b",
     "system": "You are a creative media production writer."
   }

RULES:
- Respond ONLY with the JSON object. No markdown, no code blocks, no extra text.
- The "reply" field is shown in the chat to the user — keep it warm and concise.
- For image/video: expand the user's prompt into a rich visual description in params.prompt.
- If the user's intent is ambiguous, use "chat" and ask a clarifying question in "reply".
- Adjust creative direction based on brand context if provided.

EXAMPLES:
User: "make a dragon flying over mountains" → action: "image"
User: "create a 10 second clip of waves crashing" → action: "video"
User: "say hello world in Spanish" → action: "audio"
User: "write a YouTube script about black holes" → action: "text"
User: "what is RAG?" → action: "chat"
User: "research quantum computing trends" → action: "research"
"""


async def route_message(
    message: str,
    context: str,
    history: list,
    model: str,
    ollama_url: str,
    images: list = None,
) -> dict:
    """
    Use Gemma4 to classify the user's intent and return a routing dict.
    Returns: {action, reply, params}
    """
    logger.info(f"route_message: model={model}, message='{message}', images_count={len(images) if images else 0}")
    # Build messages — include last 6 history items for context efficiency
    messages = [{"role": "system", "content": ROUTING_SYSTEM_PROMPT}]

    for h in history[-6:]:
        messages.append({
            "role": h.get("role", "user"),
            "content": h.get("content", "")
        })

    # Inject brand context as a hint alongside the user message
    context_hint = f"[Studio Brand: {context}]\n" if context and context != "Default" else ""
    user_msg = {"role": "user", "content": f"{context_hint}{message}"}
    if images:
        user_msg["images"] = images
    messages.append(user_msg)

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.05,   # Near-zero for deterministic JSON
                        "top_p": 0.9,
                        "num_predict": 2048,
                    }
                }
            )
            resp.raise_for_status()
            raw = resp.json()["message"]["content"].strip()
            logger.info(f"route_message response raw: '{raw}'")
    except httpx.RequestError as e:
        logger.error(f"Orchestrator Ollama connection error: {e}")
        return {
            "action": "chat",
            "reply": "⚠️ Cannot reach the AI model. Please check Ollama is running.",
            "params": {},
        }
    except Exception as e:
        logger.error(f"Orchestrator routing error: {e}")
        return {
            "action": "chat",
            "reply": f"Something went wrong with the orchestrator: {str(e)[:100]}",
            "params": {},
        }

    # Parse JSON — Gemma4 may occasionally wrap in ```json``` blocks
    try:
        cleaned = raw
        if "```" in cleaned:
            # Strip code fences if present
            parts = cleaned.split("```")
            for part in parts:
                stripped = part.strip()
                if stripped.startswith("json"):
                    stripped = stripped[4:].strip()
                if stripped.startswith("{"):
                    cleaned = stripped
                    break
        # Find the JSON object boundaries
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start >= 0 and end > start:
            cleaned = cleaned[start:end]
        routing = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse routing JSON from Gemma4: {e}\nRaw: {raw[:300]}")
        # Graceful fallback — treat as plain chat response
        return {
            "action": "chat",
            "reply": raw[:1000] if raw else "I couldn't parse that request. Could you rephrase?",
            "params": {},
        }

    # Map Dify/ReAct tool call schemas to Spark schemas
    action = routing.get("action", "chat")
    params = routing.get("params", {})
    reply = routing.get("reply", "")

    # Handle ReAct/Dify action_input format
    action_input = routing.get("action_input", {})
    if isinstance(action_input, str) and action_input.strip():
        try:
            action_input = json.loads(action_input)
        except Exception:
            action_input = {"prompt": action_input}

    # Extract parameters from action_input if params is empty
    if not params and isinstance(action_input, dict):
        params = action_input

    # Map Dify actions to Spark actions
    dify_action_map = {
        "dalle.text2im": "image",
        "dalle": "image",
        "sdxl": "image",
        "stable_diffusion": "image",
        "flux": "image",
        "generate_image": "image",
        "image_gen": "image",
        "text2image": "image",
        "text2im": "image",
        "video_gen": "video",
        "ltx": "video",
        "text2video": "video",
        "generate_video": "video",
        "tts": "audio",
        "text2speech": "audio",
        "generate_audio": "audio",
        "generate_speech": "audio",
        "generate_music": "music",
        "music_gen": "music",
        "generate_3d": "3d",
        "3d_gen": "3d",
        "web_search": "research",
        "search": "research",
        "generate_research": "research",
        "writer": "text",
        "generate_text": "text",
        "text_gen": "text"
    }

    if action in dify_action_map:
        action = dify_action_map[action]

    # Validate action
    valid_actions = {"chat", "image", "video", "audio", "music", "3d", "research", "text"}
    if action not in valid_actions:
        action = "chat"

    # Default friendly replies for converted tool calls
    if action != "chat" and not reply:
        friendly_replies = {
            "image": "I've formulated an image generation card for you.",
            "video": "I've prepared a video generation card for you.",
            "audio": "I can synthesize this text to audio.",
            "music": "I've drafted a music track card.",
            "research": "I'll start researching this topic.",
            "text": "I've prepared a text generation draft."
        }
        reply = friendly_replies.get(action, "Processing your request...")

    return {
        "action": action,
        "reply": reply or "Processing your request...",
        "params": params,
    }


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

async def handle_chat(
    message: str,
    context: str,
    history: list,
    model: str,
    ollama_url: str,
    images: list = None,
    active_contexts: list = None,
) -> str:
    """
    Handle a plain chat message directly via Ollama (no routing needed).
    Returns the assistant's text response.
    """
    logger.info(f"handle_chat: model={model}, message='{message}', images_count={len(images) if images else 0}, active_contexts={active_contexts}")
    messages = []
    if not images:
        system = (
            f"You are Spark AI, a creative media production assistant for {context}.\n"
            "You are integrated into the Spark Media Workstation Node 1, which provides the following production tools:\n"
            "1. Image Factory: Generate artwork using FLUX models.\n"
            "2. Video Factory: Create animations using LTX-Video.\n"
            "3. Audio Factory: Synthesize speech from text using F5-TTS.\n"
            "4. Music Factory: Generate soundtrack audio.\n"
            "5. 3D Factory: Generate 3D assets/models.\n"
            "6. Ingest & OCR: Extracted text and PDFs saved to local Qdrant RAG Memory.\n"
            "7. Research Agent: Crawl, search, and compile web research reports.\n"
            "8. Mail Agent: Sync, search, draft, and send emails via Gmail/Yahoo.\n"
            "9. Meme Factory: Generate concepts and add text overlays to images.\n"
            "10. Coding Agent: Write and run Python code safely.\n"
            "11. Voice Agent: Conversational voice-to-voice interface.\n\n"
            "Answer questions helpfully and concisely. If the user wants to generate media or run any of these tasks, "
            "simply tell them to describe what they want and you will formulate the generator parameters for them."
        )
        
        # 1. Retrieve semantic matches from Qdrant RAG collection (if available)
        try:
            from app.backends import rag
            hits = await rag.query(message, limit=3)
            if hits:
                segments = []
                for hit in hits:
                    segments.append(f"[Source File: {hit['source']}] (Score: {hit['score']:.2f}):\n{hit['text']}")
                rag_context = "\n\n".join(segments)
                system += (
                    "\n\nUse the following reference context from the user's uploaded documents/links if relevant to answer their query:\n"
                    f"{rag_context}"
                )
        except Exception as e:
            logger.warning(f"Failed to query RAG for chat context: {e}")

        # 1b. Retrieve RAG document contexts from active_contexts toggles
        if active_contexts:
            if "workbench_tools" in active_contexts:
                try:
                    tools_path = os.path.join(DATA_DIR, "workbench_tools.md")
                    if os.path.exists(tools_path):
                        with open(tools_path, "r", encoding="utf-8") as f:
                            system += f"\n\n[REFERENCE CONTEXT: WORKBENCH TOOLS GUIDE]\n{f.read()}\n"
                except Exception as e:
                    logger.warning(f"Failed to read workbench tools file: {e}")
            if "channels_info" in active_contexts:
                try:
                    channels_path = os.path.join(DATA_DIR, "channels_info.md")
                    if os.path.exists(channels_path):
                        with open(channels_path, "r", encoding="utf-8") as f:
                            system += f"\n\n[REFERENCE CONTEXT: BRAND CHANNELS GUIDE]\n{f.read()}\n"
                except Exception as e:
                    logger.warning(f"Failed to read brand channels file: {e}")
            if "network_manifest" in active_contexts:
                try:
                    manifest_path = os.path.join(DATA_DIR, "spark_master_rag_manifest.md")
                    if os.path.exists(manifest_path):
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            system += f"\n\n[REFERENCE CONTEXT: MASTER RAG MANIFEST]\n{f.read()}\n"
                except Exception as e:
                    logger.warning(f"Failed to read spark_master_rag_manifest.md: {e}")
            if "production_template" in active_contexts:
                try:
                    template_path = os.path.join(BASE_DIR, "manual", "X13_master_production_template.md")
                    if os.path.exists(template_path):
                        with open(template_path, "r", encoding="utf-8") as f:
                            system += f"\n\n[REFERENCE CONTEXT: MASTER PRODUCTION TEMPLATE]\n{f.read()}\n"
                except Exception as e:
                    logger.warning(f"Failed to read X13_master_production_template.md: {e}")
            
        # 2. Retrieve real-time system hardware status (CPU, RAM, GPU)
        if not active_contexts or "hardware_specs" in active_contexts:
            try:
                from app.backends import utils
                specs = utils.get_system_specs()
                gpus_str = ", ".join(specs.get("gpus", []))
                system += (
                    f"\n\n[Spark Workstation Node 1 System Info]\n"
                    f"- CPU Cores: {specs.get('cpu_cores')}\n"
                    f"- RAM: {specs.get('ram_free_gb')} GB free / {specs.get('ram_total_gb')} GB total\n"
                    f"- Installed GPUs: {gpus_str}\n"
                )
            except Exception as e:
                logger.warning(f"Failed to query system specs for chat context: {e}")

        messages.append({"role": "system", "content": system})

    for h in history[-10:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    user_msg = {"role": "user", "content": message}
    if images:
        user_msg["images"] = images
    messages.append(user_msg)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{ollama_url}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.7, "top_p": 0.95}
                }
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            logger.info(f"handle_chat response raw: '{content[:200]}...'")
            return content
    except Exception as e:
        logger.error(f"Chat Ollama error: {e}")
        return f"⚠️ Error connecting to {model}: {str(e)}"
