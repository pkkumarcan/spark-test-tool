import os
import uuid
import logging
import tempfile
import httpx
from fastapi import Request, HTTPException, UploadFile

logger = logging.getLogger("spark.backend.whisper_stt")


async def transcribe(request: Request, whisper_url: str):
    form = await request.form()
    file: UploadFile = form.get("file")
    language = form.get("language", "en")

    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ext = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
    temp_path = os.path.join(tempfile.gettempdir(), f"whisper_{uuid.uuid4().hex}{ext}")

    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(temp_path, "rb") as f:
                files = {"audio_file": (file.filename or "audio.wav", f, "audio/wav")}
                params = {
                    "task": "transcribe",
                    "output": "json",
                    "vad_filter": "true"
                }
                if language:
                    params["language"] = language

                r = await client.post(f"{whisper_url}/asr", files=files, params=params)

                if r.status_code == 200:
                    return r.json()
                else:
                    logger.error(f"Whisper returned {r.status_code}: {r.text}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Whisper returned {r.status_code}: {r.text}",
                    )
    except httpx.RequestError as e:
        logger.error(f"Whisper connection error: {e}")
        raise HTTPException(status_code=503, detail=f"Whisper container unreachable: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
