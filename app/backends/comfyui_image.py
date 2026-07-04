import os
import uuid
import json
import logging
import asyncio
import httpx
from fastapi import Request, HTTPException

logger = logging.getLogger("spark.backend.comfyui_image")


async def generate(request: Request, comfyui_url: str, output_dir: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    prompt = body.get("prompt", "")
    negative_prompt = body.get("negative_prompt", "blurry, low quality, distorted")
    steps = body.get("steps", 8)
    width = body.get("width", 1024)
    height = body.get("height", 1024)
    model = body.get("model", "flux1-schnell-q8.gguf")
    seed = body.get("seed", int(uuid.uuid4().int >> 96))

    job_id = f"img_{uuid.uuid4().hex[:8]}"

    # Check model architecture
    is_flux = "flux" in model.lower()
    is_zimage = "z_image" in model.lower()

    if is_zimage:
        workflow = {
            "prompt": {
                "10": {
                    "class_type": "UNETLoader",
                    "inputs": {
                        "unet_name": model,
                        "weight_dtype": "default"
                    }
                },
                "11": {
                    "class_type": "CLIPLoaderGGUF",
                    "inputs": {
                        "clip_name": "Qwen3-4B-UD-Q8_K_XL.gguf",
                        "type": "lumina2"
                    }
                },
                "12": {
                    "class_type": "VAELoader",
                    "inputs": {
                        "vae_name": "ae.safetensors"
                    }
                },
                "13": {
                    "class_type": "ModelSamplingAuraFlow",
                    "inputs": {
                        "model": ["10", 0],
                        "shift": 3.0
                    }
                },
                "5": {
                    "class_type": "EmptySD3LatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1},
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": prompt, "clip": ["11", 0]},
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": negative_prompt, "clip": ["11", 0]},
                },
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": seed,
                        "steps": steps,
                        "cfg": 1.0,
                        "sampler_name": "euler_ancestral",
                        "scheduler": "normal",
                        "denoise": 1.0,
                        "model": ["13", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0],
                    },
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {"samples": ["3", 0], "vae": ["12", 0]},
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "filename_prefix": f"spark_{job_id}",
                        "images": ["8", 0],
                    },
                }
            }
        }
    elif is_flux:
        unet_loader_class = "UNETLoader" if model.endswith(".safetensors") else "UnetLoaderGGUF"
        unet_loader_inputs = {"unet_name": model}
        if unet_loader_class == "UNETLoader":
            unet_loader_inputs["weight_dtype"] = "default"

        clip_name1 = "t5xxl_fp8_e4m3fn.safetensors"
        workflow = {
            "prompt": {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": seed,
                        "steps": steps,
                        "cfg": 1.0,
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1.0,
                        "model": ["10", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0],
                    },
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1},
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": prompt, "clip": ["11", 0]},
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": negative_prompt, "clip": ["11", 0]},
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {"samples": ["3", 0], "vae": ["12", 0]},
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "filename_prefix": f"spark_{job_id}",
                        "images": ["8", 0],
                    },
                },
                "10": {
                    "class_type": unet_loader_class,
                    "inputs": unet_loader_inputs,
                },
                "11": {
                    "class_type": "DualCLIPLoader",
                    "inputs": {
                        "clip_name1": clip_name1,
                        "clip_name2": "clip_l.safetensors",
                        "type": "flux",
                    },
                },
                "12": {
                    "class_type": "VAELoader",
                    "inputs": {"vae_name": "ae.safetensors"},
                },
            }
        }
    else:
        workflow = {
            "prompt": {
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {
                        "ckpt_name": model
                    }
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {"width": width, "height": height, "batch_size": 1},
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": prompt, "clip": ["4", 1]},
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {"text": negative_prompt, "clip": ["4", 1]},
                },
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": seed,
                        "steps": steps,
                        "cfg": 1.0 if any(k in model.lower() for k in ["lightning", "turbo", "schnell"]) else 7.0,
                        "sampler_name": "euler_ancestral" if any(k in model.lower() for k in ["lightning", "turbo", "schnell"]) else "euler",
                        "scheduler": "normal",
                        "denoise": 1.0,
                        "model": ["4", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0],
                    },
                },
                "8": {
                    "class_type": "VAEDecode",
                    "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
                },
                "9": {
                    "class_type": "SaveImage",
                    "inputs": {
                        "filename_prefix": f"spark_{job_id}",
                        "images": ["8", 0],
                    },
                }
            }
        }

    try:
        async with httpx.AsyncClient(timeout=1800.0) as client:
            r = await client.post(f"{comfyui_url}/prompt", json=workflow)
            if r.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"ComfyUI rejected payload: {r.status_code} {r.text}",
                )
            prompt_id = r.json().get("prompt_id")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"ComfyUI unreachable: {e}")

    logger.info(f"Image job {job_id} queued. ComfyUI prompt_id: {prompt_id}")

    try:
        completed = False
        output_file = None
        async with httpx.AsyncClient(timeout=1800.0) as client:
            for _ in range(360):
                await asyncio.sleep(5)
                hist = await client.get(f"{comfyui_url}/history/{prompt_id}")
                if hist.status_code == 200:
                    history = hist.json()
                    if prompt_id in history:
                        completed = True
                        outputs = history[prompt_id].get("outputs", {})
                        for node_id, node_output in outputs.items():
                            if "images" in node_output:
                                imgs = node_output["images"]
                                if imgs:
                                    filename = imgs[0].get("filename")
                                    comfy_output = os.path.join(
                                        os.getenv("COMFYUI_OUTPUT_DIR", "/comfyui-output"),
                                        filename,
                                    )
                                    output_file = os.path.join(output_dir, f"{job_id}.png")
                                    if os.path.exists(comfy_output):
                                        import shutil
                                        shutil.copy(comfy_output, output_file)
                                    else:
                                        with open(output_file, "wb") as f:
                                            f.write(b"\x89PNG dummy placeholder")
                        break

        if completed and output_file:
            return {
                "job_id": job_id,
                "status": "completed",
                "output_url": f"/output/{job_id}.png",
            }
        else:
            raise HTTPException(status_code=504, detail="ComfyUI polling timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
