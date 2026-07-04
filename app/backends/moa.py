import os
import json
import logging
import asyncio
import httpx
from fastapi import Request, HTTPException

logger = logging.getLogger("spark.backend.moa")


async def query_single_model(client: httpx.AsyncClient, ollama_url: str, model: str, prompt: str, system_prompt: str) -> dict:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    try:
        r = await client.post(f"{ollama_url}/api/chat", json=payload)
        if r.status_code == 200:
            content = r.json().get("message", {}).get("content", "").strip()
            return {"model": model, "content": content}
        return {"model": model, "content": f"[Error: Ollama returned {r.status_code}]"}
    except Exception as e:
        logger.warning(f"Failed to query model {model}: {e}")
        return {"model": model, "content": f"[Error: Unreachable - {e}]"}


async def moa_chat(request: Request, ollama_url: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    prompt = body.get("prompt", "")
    reference_models = body.get("reference_models", [])
    synthesizer_model = body.get("synthesizer_model", "")
    system_prompt = body.get("system_prompt", "You are a helpful AI assistant.")

    if not prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt is required")
    if not reference_models:
        raise HTTPException(status_code=400, detail="At least one reference model must be selected")
    if not synthesizer_model:
        raise HTTPException(status_code=400, detail="Synthesizer model is required")

    logger.info(f"Starting Mixture of Agents (MoA) for prompt. References: {reference_models} | Synthesizer: {synthesizer_model}")

    # Query all reference models in parallel
    async with httpx.AsyncClient(timeout=90.0) as client:
        tasks = [query_single_model(client, ollama_url, m, prompt, system_prompt) for m in reference_models]
        drafts = await asyncio.gather(*tasks)

    # Format drafts for synthesis prompt
    drafts_formatted = ""
    for idx, d in enumerate(drafts):
        drafts_formatted += f"--- Draft Response from Model {idx+1} ({d['model']}) ---\n{d['content']}\n\n"

    synthesis_instruction = (
        "You are an expert synthesizer and consensus aggregator. You are given a list of draft responses "
        "from other AI models to the user prompt. Your task is to analyze these drafts, combine their strengths, "
        "resolve any factual discrepancies, and output a highly cohesive, accurate, and polished final response. "
        "Cite the key insights from the drafts if appropriate, and format your output beautifully in Markdown.\n\n"
        f"User Prompt: {prompt}\n\n"
        f"Draft Responses:\n{drafts_formatted}"
    )

    synthesis_payload = {
        "model": synthesizer_model,
        "messages": [
            {"role": "user", "content": synthesis_instruction}
        ],
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=synthesis_payload)
            if r.status_code == 200:
                final_content = r.json().get("message", {}).get("content", "").strip()
                return {
                    "status": "completed",
                    "final_response": final_content,
                    "drafts": drafts
                }
            else:
                raise HTTPException(status_code=502, detail=f"Synthesizer returned {r.status_code}: {r.text}")
    except Exception as e:
        logger.error(f"MoA synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=f"MoA aggregation failed: {str(e)}")
