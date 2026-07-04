import os
import uuid
import json
import logging
import asyncio
import httpx
from fastapi import Request, HTTPException
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("spark.backend.meme_generator")


def draw_impact_text(draw, text, x, y, font, outline_color="black", fill_color="white", thickness=2):
    # Draw outline by drawing offset text in 8 directions
    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # Draw center text
    draw.text((x, y), text, font=font, fill=fill_color)


def overlay_meme_text(image_path: str, top_text: str, bottom_text: str):
    try:
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        W, H = img.size

        # Find a bold/impact font
        font_size = int(H * 0.08) # 8% of image height
        font = None
        for path in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, font_size)
                    break
                except Exception:
                    pass
        if font is None:
            font = ImageFont.load_default()

        # Draw Top Text
        if top_text.strip():
            top_text = top_text.upper()
            try:
                # Try getting text bbox for centering
                bbox = draw.textbbox((0, 0), top_text, font=font)
                w = bbox[2] - bbox[0]
            except Exception:
                # fallback for older PIL versions
                w = draw.textlength(top_text, font=font) if hasattr(draw, "textlength") else font_size * len(top_text) * 0.5
            x = (W - w) / 2
            y = int(H * 0.05)
            draw_impact_text(draw, top_text, x, y, font, thickness=3)

        # Draw Bottom Text
        if bottom_text.strip():
            bottom_text = bottom_text.upper()
            try:
                bbox = draw.textbbox((0, 0), bottom_text, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
            except Exception:
                w = draw.textlength(bottom_text, font=font) if hasattr(draw, "textlength") else font_size * len(bottom_text) * 0.5
                h = font_size
            x = (W - w) / 2
            y = H - h - int(H * 0.08)
            draw_impact_text(draw, bottom_text, x, y, font, thickness=3)

        img.save(image_path)
        logger.info(f"Successfully overlaid meme text on image: {image_path}")
    except Exception as e:
        logger.error(f"Failed to overlay meme text: {e}")


async def generate_meme(request: Request, ollama_url: str, comfyui_url: str, output_dir: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    return await generate_meme_from_params(body, ollama_url, comfyui_url, output_dir)


async def generate_meme_from_params(body: dict, ollama_url: str, comfyui_url: str, output_dir: str):

    topic = body.get("prompt", "")
    image_model = body.get("image_model", "flux1-schnell-q8.gguf")

    if not topic.strip():
        raise HTTPException(status_code=400, detail="Topic prompt is required")

    job_id = f"meme_{uuid.uuid4().hex[:8]}"

    # Step 1: Generate meme prompts via LLM
    logger.info(f"[{job_id}] Step 1: Formulating meme concepts via Ollama...")
    system_prompt = (
        "You are a meme designer. Based on the topic provided, generate a meme concept.\n"
        "Output exactly a JSON object with three fields:\n"
        "1. 'top_text': The text caption at the top of the meme (witty, humorous).\n"
        "2. 'bottom_text': The text caption at the bottom of the meme (punchline).\n"
        "3. 'image_prompt': A descriptive visual prompt to generate a funny background image for the meme. Keep it simple and clean.\n"
        "Do not write any introductory or concluding text."
    )

    ollama_payload = {
        "model": "qwen3:8b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Meme Topic: {topic}"}
        ],
        "format": "json",
        "stream": False
    }

    # Query tags to pick model
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{ollama_url}/api/tags")
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if "qwen3:8b" in models:
                    ollama_payload["model"] = "qwen3:8b"
                elif "qwen3:14b" in models:
                    ollama_payload["model"] = "qwen3:14b"
                elif models:
                    ollama_payload["model"] = models[0]
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{ollama_url}/api/chat", json=ollama_payload)
            if r.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Ollama meme gen failed: {r.text}")
            content = r.json().get("message", {}).get("content", "").strip()
            meme_data = json.loads(content)
    except Exception as e:
        logger.error(f"Failed to generate meme concept: {e}")
        raise HTTPException(status_code=500, detail=f"Meme LLM generation failed: {str(e)}")

    top_text = meme_data.get("top_text", "")
    bottom_text = meme_data.get("bottom_text", "")
    img_prompt = meme_data.get("image_prompt", topic)

    logger.info(f"[{job_id}] Concept: Top: '{top_text}' | Bottom: '{bottom_text}' | Visual Prompt: '{img_prompt}'")

    # Step 2: Render background image via ComfyUI (Flux Schnell)
    logger.info(f"[{job_id}] Step 2: Rendering background image...")
    image_file = os.path.join(output_dir, f"{job_id}.png")
    
    # We construct a minimal ComfyUI workflow for Flux Schnell
    workflow = {
        "prompt": {
            "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": image_model}},
            "11": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "t5xxl_fp8_e4m3fn.safetensors", "clip_name2": "clip_l.safetensors", "type": "flux"}},
            "12": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": img_prompt, "clip": ["11", 0]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality", "clip": ["11", 0]}},
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 1337, "steps": 4, "cfg": 1.0, "sampler_name": "euler",
                    "scheduler": "normal", "denoise": 1.0, "model": ["10", 0],
                    "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]
                }
            },
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": job_id, "images": ["8", 0]}}
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{comfyui_url}/prompt", json=workflow)
            if r.status_code != 200:
                raise Exception(f"ComfyUI prompt submit rejected: {r.text}")
            prompt_id = r.json().get("prompt_id")
            
            # Poll history
            completed = False
            for _ in range(60):
                await asyncio.sleep(2)
                hist = await client.get(f"{comfyui_url}/history/{prompt_id}")
                if hist.status_code == 200:
                    history = hist.json()
                    if prompt_id in history:
                        completed = True
                        outputs = history[prompt_id].get("outputs", {})
                        for node_id, node_output in outputs.items():
                            if "images" in node_output and node_output["images"]:
                                filename = node_output["images"][0].get("filename")
                                comfy_output = os.path.join(
                                    os.getenv("COMFYUI_OUTPUT_DIR", "/comfyui-output"),
                                    filename,
                                )
                                if os.path.exists(comfy_output):
                                    import shutil
                                    shutil.copy(comfy_output, image_file)
                        break
            if not completed or not os.path.exists(image_file):
                raise Exception("ComfyUI polling timed out or image missing")
    except Exception as e:
        logger.error(f"Background image generation failed: {e}")
        raise HTTPException(status_code=502, detail=f"Image rendering failed: {e}")

    # Step 3: Draw Overlay text on image
    logger.info(f"[{job_id}] Step 3: Overlaying impact text captions...")
    overlay_meme_text(image_file, top_text, bottom_text)

    return {
        "job_id": job_id,
        "status": "completed",
        "output_url": f"/output/{job_id}.png",
        "top_text": top_text,
        "bottom_text": bottom_text,
        "image_prompt": img_prompt
    }
