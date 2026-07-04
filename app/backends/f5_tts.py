import os
import uuid
import json
import logging
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger("spark.backend.f5_tts")


async def speak(request: Request, f5_tts_url: str, output_dir: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    text = body.get("text", "")
    voice = body.get("voice", "default")
    speed = body.get("speed", 1.0)

    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    job_id = f"tts_{uuid.uuid4().hex[:8]}"
    output_file = os.path.join(output_dir, f"{job_id}.wav")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "text": text,
                "voice": voice,
                "speed": speed,
            }
            r = await client.post(f"{f5_tts_url}/synthesize", json=payload)

            if r.status_code == 200:
                content_type = r.headers.get("content-type", "")
                if "audio" in content_type or "wav" in content_type or "octet-stream" in content_type:
                    with open(output_file, "wb") as f:
                        f.write(r.content)
                    return FileResponse(
                        output_file,
                        media_type="audio/wav",
                        filename=f"{job_id}.wav",
                    )
                else:
                    result = r.json()
                    if "audio_path" in result:
                        audio_path = result["audio_path"]
                        if os.path.exists(audio_path):
                            import shutil
                            shutil.copy(audio_path, output_file)
                            return FileResponse(
                                output_file,
                                media_type="audio/wav",
                                filename=f"{job_id}.wav",
                            )
                    raise HTTPException(
                        status_code=502,
                        detail=f"F5-TTS returned unexpected response: {r.text[:200]}",
                    )
            else:
                logger.error(f"F5-TTS returned {r.status_code}: {r.text}")
                raise HTTPException(
                    status_code=502,
                    detail=f"F5-TTS returned {r.status_code}: {r.text}",
                )
    except httpx.RequestError as e:
        logger.error(f"F5-TTS connection error: {e}")
        raise HTTPException(status_code=503, detail=f"F5-TTS container unreachable: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
