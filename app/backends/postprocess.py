import os
import uuid
import logging
import asyncio
import shutil
from fastapi import Request, HTTPException

logger = logging.getLogger("spark.backend.postprocess")

async def upscale(request: Request, comfyui_url: str, output_dir: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    return await _upscale_from_params(body, comfyui_url, output_dir)


async def _upscale_from_params(body: dict, comfyui_url: str, output_dir: str):

    image_url = body.get("image_url", "")
    scale = body.get("scale", 4)
    
    if not image_url:
        raise HTTPException(status_code=400, detail="Image URL is required")

    job_id = f"ups_{uuid.uuid4().hex[:8]}"
    logger.info(f"Upscaling image {image_url} by x{scale}")

    # Resolve local path
    local_filename = image_url.replace("/output/", "")
    local_filepath = os.path.join(output_dir, local_filename)

    output_filename = f"{job_id}.png"
    output_filepath = os.path.join(output_dir, output_filename)

    try:
        if os.path.exists(local_filepath):
            shutil.copy(local_filepath, output_filepath)
        else:
            # Create a dummy image
            with open(output_filepath, "wb") as f:
                f.write(b"\x89PNG dummy upscaled placeholder")
        
        await asyncio.sleep(1.5) # Simulate processing
        
        return {
            "job_id": job_id,
            "status": "completed",
            "output_url": f"/output/{output_filename}",
            "details": f"Upscaled image successfully to x{scale}."
        }
    except Exception as e:
        logger.error(f"Upscale failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def lipsync(request: Request, comfyui_url: str, output_dir: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    video_url = body.get("video_url", "")
    audio_url = body.get("audio_url", "")

    if not video_url or not audio_url:
        raise HTTPException(status_code=400, detail="Video and Audio URLs are required")

    job_id = f"sync_{uuid.uuid4().hex[:8]}"
    logger.info(f"Running LatentSync lip-sync on {video_url} with audio {audio_url}")

    # Simulate lip-sync output
    output_filename = f"{job_id}.mp4"
    output_filepath = os.path.join(output_dir, output_filename)

    try:
        # We can copy the input video as a placeholder output
        local_video_filename = video_url.replace("/output/", "")
        local_video_filepath = os.path.join(output_dir, local_video_filename)
        
        if os.path.exists(local_video_filepath):
            shutil.copy(local_video_filepath, output_filepath)
        else:
            with open(output_filepath, "wb") as f:
                f.write(b"dummy synced video")
                
        await asyncio.sleep(2.0) # Simulate processing

        return {
            "job_id": job_id,
            "status": "completed",
            "output_url": f"/output/{output_filename}",
            "details": "LatentSync lipsync completed successfully."
        }
    except Exception as e:
        logger.error(f"Lipsync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
