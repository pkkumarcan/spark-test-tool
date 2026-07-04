import os
import uuid
import logging
import tempfile
import httpx
from fastapi import Request, HTTPException, UploadFile, File

logger = logging.getLogger("spark.backend.voice_agent")

async def run_voice_agent(
    file: UploadFile, 
    ollama_url: str, 
    whisper_url: str, 
    f5_tts_url: str, 
    output_dir: str
):
    logger.info(f"Voice Agent received audio file {file.filename}")

    # Step 1: Transcribe user audio via Whisper
    ext = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    temp_path = os.path.join(tempfile.gettempdir(), f"voice_{uuid.uuid4().hex}{ext}")

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        user_text = ""
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(temp_path, "rb") as f:
                files = {"audio_file": (file.filename or "audio.wav", f, "audio/wav")}
                params = {"task": "transcribe", "output": "json", "vad_filter": "true"}
                r = await client.post(f"{whisper_url}/asr", files=files, params=params)
                if r.status_code == 200:
                    user_text = r.json().get("text", "").strip()
                else:
                    logger.error(f"Whisper returned status {r.status_code} in voice loop")
                    raise Exception(f"Whisper error: {r.text}")
    except Exception as e:
        logger.error(f"Voice Agent Whisper stage failed: {e}")
        raise HTTPException(status_code=502, detail=f"Failed to transcribe user voice input: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not user_text:
        return {
            "status": "ignored",
            "user_text": "",
            "agent_text": "I couldn't hear you clearly. Could you please repeat that?",
            "audio_url": None
        }

    logger.info(f"Voice Agent transcribed user text: '{user_text}'")

    # Step 2: Generate response text via Ollama
    system_prompt = (
        "You are a helpful, conversational, and very concise voice assistant. "
        "Keep your response short and sweet (exactly 1 to 2 sentences maximum) so it is natural to listen to."
    )

    ollama_payload = {
        "model": "qwen3:8b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
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

    agent_text = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=ollama_payload)
            if r.status_code == 200:
                agent_text = r.json().get("message", {}).get("content", "").strip()
            else:
                raise Exception(f"Ollama returned {r.status_code}")
    except Exception as e:
        logger.error(f"Voice Agent Ollama stage failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate assistant response: {str(e)}")

    logger.info(f"Voice Agent reply: '{agent_text}'")

    # Step 3: Synthesize assistant response voice via F5-TTS
    job_id = f"tts_{uuid.uuid4().hex[:8]}"
    output_filename = f"{job_id}.wav"
    output_file_path = os.path.join(output_dir, output_filename)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "text": agent_text,
                "voice": "default",
                "speed": 1.0
            }
            r = await client.post(f"{f5_tts_url}/synthesize", json=payload)
            if r.status_code == 200:
                content_type = r.headers.get("content-type", "")
                if "audio" in content_type or "wav" in content_type or "octet-stream" in content_type:
                    with open(output_file_path, "wb") as f:
                        f.write(r.content)
                else:
                    result = r.json()
                    if "audio_path" in result and os.path.exists(result["audio_path"]):
                        shutil.copy(result["audio_path"], output_file_path)
                    else:
                        raise Exception("No audio file returned in F5-TTS response")
            else:
                raise Exception(f"F5-TTS returned {r.status_code}: {r.text}")
    except Exception as e:
        logger.error(f"Voice Agent F5-TTS stage failed: {e}")
        # Return text response even if TTS synthesis fails, but set audio_url to null
        return {
            "status": "tts_error",
            "user_text": user_text,
            "agent_text": agent_text,
            "audio_url": None,
            "details": f"Text reply generated but voice synthesis failed: {str(e)}"
        }

    return {
        "status": "success",
        "user_text": user_text,
        "agent_text": agent_text,
        "audio_url": f"/output/{output_filename}"
    }
