import os
import json
import logging
import time
import httpx
from fastapi import Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger("spark.backend.ollama")

async def list_models(ollama_url: str):
    models = []
    errors = []
    
    # 1. Fetch from Ollama
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{ollama_url}/api/tags")
            if r.status_code == 200:
                models.extend([m["name"] for m in r.json().get("models", [])])
            else:
                errors.append(f"Ollama returned {r.status_code}")
    except Exception as e:
        errors.append(f"Ollama connection error: {str(e)}")
        
    # 2. Fetch from vLLM (OpenAI-compatible)
    vllm_url = os.getenv("VLLM_URL", "http://host.docker.internal:8000")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{vllm_url}/v1/models")
            if r.status_code == 200:
                vllm_data = r.json().get("data", [])
                models.extend([f"vllm/{m['id']}" for m in vllm_data])
    except Exception as e:
        logger.debug(f"vLLM is offline or unreachable: {e}")
        
    return {"models": models, "errors": errors if errors else None}


async def chat(request: Request, ollama_url: str):
    try:
        body = await request.json()
    except Exception:
        return {"error": "Invalid JSON body"}

    messages = body.get("messages", [])
    model = body.get("model", "qwen3.6:27b")
    system_prompt = body.get("system_prompt", "You are a helpful AI assistant.")
    rag_enabled = body.get("rag", False)

    # 1. RAG Context Injection
    if rag_enabled and len(messages) > 0:
        try:
            from app.backends import rag
            query_text = messages[-1].get("content", "")
            hits = await rag.query(query_text)
            if hits:
                context_str = "\n\n".join([f"Source: {h['source']} (Tool: {h['tool']})\n{h['text']}" for h in hits])
                system_prompt += f"\n\n[RETRIEVED CONTEXT MEMORY]\nUse this context to inform your answer:\n{context_str}\n"
                logger.info(f"Injected {len(hits)} RAG chunks into prompt.")
        except Exception as e:
            logger.error(f"Failed to inject RAG context: {e}")

    # 2. DeepSeek API Routing
    if model == "deepseek-v4-flash":
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if not api_key:
            async def key_generator():
                yield f"data: {json.dumps({'error': 'DEEPSEEK_API_KEY is not set in the environment variables.'})}\n\n"
            return StreamingResponse(key_generator(), media_type="text/event-stream")
            
        payload = {
            "model": "deepseek-chat", # mapped to deepseek-chat on their endpoint
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": True
        }
        
        async def deepseek_event_generator():
            full_response = []
            start_time = time.time()
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream(
                        "POST", 
                        "https://api.deepseek.com/v1/chat/completions", 
                        json=payload, 
                        headers=headers
                    ) as response:
                        if response.status_code != 200:
                            yield f"data: {json.dumps({'error': f'DeepSeek API returned {response.status_code}'})}\n\n"
                            return
                        async for line in response.aiter_lines():
                            if await request.is_disconnected():
                                logger.info("Client disconnected. Aborting DeepSeek stream.")
                                break
                            if line.startswith("data: "):
                                if "[DONE]" in line:
                                    continue
                                try:
                                    data = json.loads(line[6:])
                                    content = data["choices"][0]["delta"].get("content", "")
                                    if content:
                                        full_response.append(content)
                                    yield f"data: {json.dumps({'message': {'content': content}})}\n\n"
                                except Exception:
                                    pass
                
                # Trace event
                from app.backends.telemetry import trace_generation
                trace_generation(
                    name="chat-deepseek",
                    model=model,
                    prompt=str(messages),
                    completion="".join(full_response),
                    latency_seconds=time.time() - start_time,
                    system_prompt=system_prompt
                )
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(deepseek_event_generator(), media_type="text/event-stream")

    # 2.5. vLLM API Routing
    vllm_url = os.getenv("VLLM_URL", "http://host.docker.internal:8000")
    if model.startswith("vllm/"):
        real_model = model[5:] # Strip "vllm/"
        payload = {
            "model": real_model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "stream": True
        }
        
        async def vllm_event_generator():
            full_response = []
            start_time = time.time()
            try:
                headers = {"Content-Type": "application/json"}
                async with httpx.AsyncClient(timeout=120.0) as client:
                    async with client.stream(
                        "POST", 
                        f"{vllm_url}/v1/chat/completions", 
                        json=payload, 
                        headers=headers
                    ) as response:
                        if response.status_code != 200:
                            yield f"data: {json.dumps({'error': f'vLLM API returned {response.status_code}'})}\n\n"
                            return
                        async for line in response.aiter_lines():
                            if await request.is_disconnected():
                                logger.info("Client disconnected. Aborting vLLM stream.")
                                break
                            if line.startswith("data: "):
                                if "[DONE]" in line:
                                    continue
                                try:
                                    data = json.loads(line[6:])
                                    content = data["choices"][0]["delta"].get("content", "")
                                    if content:
                                        full_response.append(content)
                                    yield f"data: {json.dumps({'message': {'content': content}})}\n\n"
                                except Exception:
                                    pass
                
                # Trace event
                from app.backends.telemetry import trace_generation
                trace_generation(
                    name="chat-vllm",
                    model=model,
                    prompt=str(messages),
                    completion="".join(full_response),
                    latency_seconds=time.time() - start_time,
                    system_prompt=system_prompt
                )
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(vllm_event_generator(), media_type="text/event-stream")


    # 3. Default Ollama Routing
    chat_messages = []
    if system_prompt:
        chat_messages.append({"role": "system", "content": system_prompt})
    for msg in messages:
        chat_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    payload = {"model": model, "messages": chat_messages, "stream": True}

    async def event_generator():
        full_response = []
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", f"{ollama_url}/api/chat", json=payload) as response:
                    if response.status_code != 200:
                        yield f"data: {json.dumps({'error': f'Ollama returned {response.status_code}'})}\n\n"
                        return
                    async for line in response.aiter_lines():
                        if await request.is_disconnected():
                            logger.info("Client disconnected. Aborting Ollama stream.")
                            break
                        if line:
                            yield f"data: {line}\n\n"
                            try:
                                data = json.loads(line)
                                chunk = data.get("message", {}).get("content", "")
                                if chunk:
                                    full_response.append(chunk)
                            except Exception:
                                pass
            
            # Trace event
            from app.backends.telemetry import trace_generation
            trace_generation(
                name="chat-ollama",
                model=model,
                prompt=str(messages),
                completion="".join(full_response),
                latency_seconds=time.time() - start_time,
                system_prompt=system_prompt
            )
        except httpx.RequestError as e:
            logger.error(f"Ollama connection error: {e}")
            yield f"data: {json.dumps({'error': f'Connection to Ollama failed: {str(e)}'})}\n\n"
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def enhance(request: Request, ollama_url: str):
    try:
        body = await request.json()
    except Exception:
        return {"error": "Invalid JSON body"}

    prompt = body.get("prompt", "")
    model = body.get("model", "llama3.2:latest")

    if not prompt:
        return {"error": "Prompt is required"}

    system_prompt = (
        "You are an expert prompt engineer for video generation models. "
        "Rewrite the user's rough description into a highly detailed, sensory-rich prompt "
        "optimized for T5-XXL. Output only the enhanced prompt without any conversational text, "
        "introductory remarks, or explanations."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    start_time = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=payload)
            if r.status_code == 200:
                result = r.json()
                enhanced_prompt = result.get("message", {}).get("content", "").strip()
                
                # Telemetry
                from app.backends.telemetry import trace_generation
                trace_generation(
                    name="enhance-prompt",
                    model=model,
                    prompt=prompt,
                    completion=enhanced_prompt,
                    latency_seconds=time.time() - start_time,
                    system_prompt=system_prompt
                )
                
                return {"enhanced_prompt": enhanced_prompt}
            return {"error": f"Ollama returned {r.status_code}"}
    except Exception as e:
        logger.error(f"Failed to enhance prompt: {e}")
        return {"error": str(e)}

