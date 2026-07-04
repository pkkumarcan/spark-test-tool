import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
# Ensure OLLAMA_URL includes /api/chat endpoint
if not OLLAMA_URL.endswith("/api/chat"):
    OLLAMA_CHAT_URL = OLLAMA_URL.rstrip("/") + "/api/chat"
else:
    OLLAMA_CHAT_URL = OLLAMA_URL
VLLM_URL = os.getenv("VLLM_URL", "http://host.docker.internal:8000/v1/chat/completions")

RETRY_ATTEMPTS = 3
RETRY_DELAYS = [2, 4, 8]

MAX_CHARS_PER_TOKEN = 4


class LLMError(Exception):
    pass


class LLMClient:
    async def chat(
        self,
        messages: list[dict],
        model: str = "llama3",
        json_mode: bool = False,
        stream: bool = False,
        timeout: int = 120,
    ) -> dict | AsyncGenerator:
        is_vllm = model.startswith("vllm/")
        base_model = model.removeprefix("vllm/")

        if stream:
            return self._stream(messages, base_model, is_vllm, json_mode, timeout)

        payload = self._build_payload(messages, base_model, is_vllm, json_mode, stream=False)
        url = VLLM_URL if is_vllm else OLLAMA_CHAT_URL

        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                return self._parse_response(data, base_model, is_vllm)
            except (httpx.HTTPStatusError, httpx.RequestError, KeyError) as exc:
                if attempt < RETRY_ATTEMPTS - 1:
                    delay = RETRY_DELAYS[attempt]
                    logger.warning("LLM request failed (%s), retrying in %ds", exc, delay)
                    await asyncio.sleep(delay)
                else:
                    raise LLMError(f"All {RETRY_ATTEMPTS} attempts failed: {exc}") from exc

    async def _stream(self, messages, model, is_vllm, json_mode, timeout):
        payload = self._build_payload(messages, model, is_vllm, json_mode, stream=True)
        url = VLLM_URL if is_vllm else OLLAMA_CHAT_URL

        for attempt in range(RETRY_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    async with client.stream("POST", url, json=payload) as resp:
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line:
                                continue
                            if is_vllm:
                                chunk = json.loads(line.removeprefix("data: ").strip())
                                delta = chunk["choices"][0].get("delta", {})
                                token = delta.get("content", "")
                                done = chunk.get("choices", [{}])[0].get("finish_reason") is not None
                            else:
                                chunk = json.loads(line)
                                token = chunk.get("message", {}).get("content", "")
                                done = chunk.get("done", False)
                            yield {"token": token, "done": done}
                return
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                if attempt < RETRY_ATTEMPTS - 1:
                    delay = RETRY_DELAYS[attempt]
                    logger.warning("LLM stream failed (%s), retrying in %ds", exc, delay)
                    await asyncio.sleep(delay)
                else:
                    raise LLMError(f"Stream failed after {RETRY_ATTEMPTS} attempts: {exc}") from exc

    def _build_payload(self, messages, model, is_vllm, json_mode, stream=False):
        if is_vllm:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
        else:
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
            }
            if json_mode:
                payload["format"] = "json"
        return payload

    def _parse_response(self, data, model, is_vllm):
        try:
            if is_vllm:
                content = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
            else:
                content = data["message"]["content"]
                tokens_used = self._estimate_tokens(content)
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Unexpected response format: {exc}") from exc
        return {"content": content, "tokens_used": tokens_used, "model": model}

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return len(text) // MAX_CHARS_PER_TOKEN
