import os
import logging
import httpx
import re
from fastapi import Request, HTTPException

logger = logging.getLogger("spark.backend.generative_ui")

async def generate_ui_component(request: Request, ollama_url: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    prompt = body.get("prompt", "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    logger.info(f"Generating UI component for prompt: '{prompt}'")

    system_prompt = (
        "You are an expert frontend engineer. Generate a single, fully self-contained, and interactive "
        "HTML page based on the user's prompt. The page must include CSS styling inside a <style> block and "
        "JavaScript interaction inside a <script> block. Ensure it looks beautiful, modern, uses premium CSS styles "
        "(e.g., dark theme, glassmorphism, nice gradients, sleek typography), and behaves responsively.\n\n"
        "Return ONLY the self-contained HTML page code, enclosed inside a standard markdown html code block:\n"
        "```html\n<!DOCTYPE html>...\n```"
    )

    ollama_payload = {
        "model": "qwen3:8b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    # Model resolution
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{ollama_url}/api/tags")
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if "qwen3:14b" in models:
                    ollama_payload["model"] = "qwen3:14b"
                elif "qwen3:8b" in models:
                    ollama_payload["model"] = "qwen3:8b"
                elif models:
                    ollama_payload["model"] = models[0]
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=ollama_payload)
            if r.status_code == 200:
                content = r.json().get("message", {}).get("content", "").strip()
                
                # Extract HTML block from response
                html_code = ""
                html_match = re.search(r'```html\s*(.*?)\s*```', content, flags=re.DOTALL | re.IGNORECASE)
                if html_match:
                    html_code = html_match.group(1).strip()
                else:
                    # Fallback if the model didn't use codeblocks
                    if "<!DOCTYPE html>" in content or "<html" in content:
                        html_code = content
                    else:
                        html_code = f"<html><body><pre>{content}</pre></body></html>"

                return {
                    "status": "completed",
                    "html": html_code,
                    "raw_response": content
                }
            else:
                raise HTTPException(status_code=502, detail=f"Ollama returned {r.status_code}")
    except Exception as e:
        logger.error(f"Generative UI prompt failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
