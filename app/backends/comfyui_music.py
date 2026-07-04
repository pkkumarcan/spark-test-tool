import os
import uuid
import logging
import asyncio
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger("spark.backend.comfyui_music")

async def generate(request: Request, comfyui_url: str, output_dir: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    return await _generate_from_params(body, comfyui_url, output_dir)


async def _generate_from_params(body: dict, comfyui_url: str, output_dir: str):

    prompt = body.get("prompt", "")
    lyrics = body.get("lyrics", "")
    model = body.get("model", "ace-step-1.5-base")
    steps = body.get("steps", 27)
    job_id = f"mus_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"Generating music {job_id} using {model} with prompt: {prompt}")

    output_filename = f"{job_id}.mp3"
    output_filepath = os.path.join(output_dir, output_filename)

    try:
        # Create a mock mp3 file (silence or dummy tone) for testing
        # We can write simple dummy bytes
        dummy_mp3_header = b"\xFF\xFB\x90\x44\x00\x00\x00\x00"
        with open(output_filepath, "wb") as f:
            f.write(dummy_mp3_header)
            
        await asyncio.sleep(2) # Simulate generation

        return {
            "job_id": job_id,
            "status": "completed",
            "output_url": f"/output/{output_filename}",
            "details": f"Generated song with {model} successfully."
        }
    except Exception as e:
        logger.error(f"Music generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
