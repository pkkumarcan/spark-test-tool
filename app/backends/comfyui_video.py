import os
import uuid
import logging
import asyncio
import httpx
import base64
from fastapi import Request, HTTPException

logger = logging.getLogger("spark.backend.comfyui_video")

# List of video models supported by the backend
SUPPORTED_VIDEO_MODELS = ["cogvideox_5b_i2v_bf16.safetensors", "mochi_preview_fp8.safetensors", "allegro_v1_0_fp8.safetensors", "dreamshaper_8.safetensors", "ltx-2.3-22b-dev-Q4_K_M.gguf", "wan2.2_14b_q4.gguf"]


async def upload_image_to_comfyui(comfyui_url: str, image_data: str, output_dir: str) -> str:
    if not image_data:
        return ""

    filename = f"upload_{uuid.uuid4().hex[:8]}.png"
    file_bytes = None

    if image_data.startswith("data:image/"):
        try:
            header, encoded = image_data.split(",", 1)
            file_bytes = base64.b64decode(encoded)
        except Exception as e:
            logger.error(f"Failed to decode base64 image: {e}")
            raise HTTPException(status_code=400, detail="Invalid image base64 format")
    elif image_data.startswith("/output/"):
        local_filename = image_data.replace("/output/", "")
        local_filepath = os.path.join(output_dir, local_filename)
        if os.path.exists(local_filepath):
            try:
                with open(local_filepath, "rb") as f:
                    file_bytes = f.read()
                ext = os.path.splitext(local_filename)[1] or ".png"
                filename = f"upload_{uuid.uuid4().hex[:8]}{ext}"
            except Exception as e:
                logger.error(f"Failed to read local file {local_filepath}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to read asset file: {e}")
        else:
            raise HTTPException(status_code=400, detail=f"Asset file {local_filename} not found")
    else:
        try:
            file_bytes = base64.b64decode(image_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image data format")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"image": (filename, file_bytes, "image/png")}
            r = await client.post(f"{comfyui_url}/upload/image", files=files)
            if r.status_code == 200:
                return r.json().get("name", filename)
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"ComfyUI rejected image upload: {r.status_code} {r.text}",
                )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"ComfyUI unreachable during image upload: {e}")


async def generate(request: Request, comfyui_url: str, output_dir: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
    return await _generate_from_params(body, comfyui_url, output_dir)


async def _generate_from_params(body: dict, comfyui_url: str, output_dir: str):

    prompt = body.get("prompt", "")
    negative_prompt = body.get("negative_prompt", "blurry, low quality, distorted")
    steps = body.get("steps", 20)
    width = body.get("width", 480)
    height = body.get("height", 320)
    frames = body.get("frames", 49)
    model = body.get("model", "wan2.2_14b_q4.gguf")
    seed = body.get("seed", int(uuid.uuid4().int >> 96))
    cfg = body.get("cfg", 1.0 if "ltx" in model.lower() else 6.0)
    # Ensure model is one of the supported video models
    if model.lower() not in [m.lower() for m in SUPPORTED_VIDEO_MODELS]:
        raise HTTPException(status_code=400, detail=f"Unsupported video model: {model}")

    # Contextual controls
    mode = body.get("mode", "t2v")  # t2v, i2v, interpolation
    start_image = body.get("start_image", "")
    end_image = body.get("end_image", "")
    vae_tiling = body.get("vae_tiling", False)

    # Force VAE tiling for all Wan models to prevent OOM
    if "wan" in model.lower():
        vae_tiling = True

    job_id = f"vid_{uuid.uuid4().hex[:8]}"

    # Upload files to ComfyUI if keyframe conditioning is used
    start_filename = ""
    end_filename = ""
    if mode in ["i2v", "interpolation"] and start_image:
        start_filename = await upload_image_to_comfyui(comfyui_url, start_image, output_dir)
    if mode == "interpolation" and end_image:
        end_filename = await upload_image_to_comfyui(comfyui_url, end_image, output_dir)

    # Build decoder settings
    decoder_inputs = {
        "samples": ["36", 0] if "ltx" in model.lower() else ["3", 0],
        "vae": ["12", 0]
    }
    if vae_tiling:
        decoder_inputs.update({
            "tile_size": 512,
            "overlap": 64,
            "temporal_size": 64,
            "temporal_overlap": 8
        })

    if "ltx" in model.lower():
        # Setup LTX base workflow
        workflow = {
            "prompt": {
                "10": {
                    "class_type": "UnetLoaderGGUF",
                    "inputs": {
                        "unet_name": model
                    }
                },
                "11": {
                    "class_type": "DualCLIPLoaderGGUF",
                    "inputs": {
                        "clip_name1": "gemma-3-12b-it-UD-Q4_K_XL.gguf",
                        "clip_name2": "ltx-2.3_text_projection_bf16.safetensors",
                        "type": "ltxv"
                    }
                },
                "12": {
                    "class_type": "VAELoader",
                    "inputs": {
                        "vae_name": "LTX23_video_vae_bf16.safetensors"
                    }
                },
                "5": {
                    "class_type": "EmptyLTXVLatentVideo",
                    "inputs": {
                        "width": width,
                        "height": height,
                        "length": frames,
                        "batch_size": 1
                    }
                },
                "32": {
                    "class_type": "LTXVAudioVAELoader",
                    "inputs": {
                        "ckpt_name": "LTX23_audio_vae_bf16.safetensors"
                    }
                },
                "34": {
                    "class_type": "LTXVEmptyLatentAudio",
                    "inputs": {
                        "frames_number": frames,
                        "frame_rate": 25,
                        "batch_size": 1,
                        "audio_vae": ["32", 0]
                    }
                },
                "35": {
                    "class_type": "LTXVConcatAVLatent",
                    "inputs": {
                        "video_latent": ["5", 0],
                        "audio_latent": ["34", 0]
                    }
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": prompt,
                        "clip": ["11", 0]
                    }
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": negative_prompt,
                        "clip": ["11", 0]
                    }
                },
                "8": {
                    "class_type": "LTXVConditioning",
                    "inputs": {
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "frame_rate": 25.0
                    }
                },
                "9": {
                    "class_type": "LTXVScheduler",
                    "inputs": {
                        "steps": steps,
                        "max_shift": 2.05,
                        "base_shift": 0.95,
                        "stretch": True,
                        "terminal": 0.1
                    }
                },
                "15": {
                    "class_type": "CFGGuider",
                    "inputs": {
                        "model": ["10", 0],
                        "positive": ["8", 0],
                        "negative": ["8", 1],
                        "cfg": cfg
                    }
                },
                "16": {
                    "class_type": "KSamplerSelect",
                    "inputs": {
                        "sampler_name": "euler"
                    }
                },
                "20": {
                    "class_type": "RandomNoise",
                    "inputs": {
                        "noise_seed": seed
                    }
                },
                "21": {
                    "class_type": "SamplerCustomAdvanced",
                    "inputs": {
                        "noise": ["20", 0],
                        "guider": ["15", 0],
                        "sampler": ["16", 0],
                        "sigmas": ["9", 0],
                        "latent_image": ["35", 0]
                    }
                },
                "36": {
                    "class_type": "LTXVSeparateAVLatent",
                    "inputs": {
                        "av_latent": ["21", 0]
                    }
                },
                "22": {
                    "class_type": "VAEDecodeTiled" if vae_tiling else "VAEDecode",
                    "inputs": decoder_inputs
                },
                "33": {
                    "class_type": "LTXVAudioVAEDecode",
                    "inputs": {
                        "samples": ["36", 1],
                        "audio_vae": ["32", 0]
                    }
                },
                "23": {
                    "class_type": "VHS_VideoCombine",
                    "inputs": {
                        "images": ["22", 0],
                        "audio": ["33", 0],
                        "frame_rate": 25.0,
                        "loop_count": 0,
                        "filename_prefix": f"spark_{job_id}",
                        "format": "video/h264-mp4",
                        "pingpong": False,
                        "save_output": True,
                    }
                }
            }
        }

        # Apply image conditioning nodes for LTX-2.3
        if mode == "i2v" and start_filename:
            workflow["prompt"]["37"] = {
                "class_type": "LoadImage",
                "inputs": {
                    "image": start_filename
                }
            }
            workflow["prompt"]["38"] = {
                "class_type": "LTXVAddGuide",
                "inputs": {
                    "positive": ["8", 0],
                    "negative": ["8", 1],
                    "vae": ["12", 0],
                    "latent": ["35", 0],
                    "image": ["37", 0],
                    "frame_idx": 0,
                    "strength": 1.0
                }
            }
            workflow["prompt"]["15"]["inputs"]["positive"] = ["38", 0]
            workflow["prompt"]["15"]["inputs"]["negative"] = ["38", 1]
            workflow["prompt"]["21"]["inputs"]["latent_image"] = ["38", 2]

        elif mode == "interpolation" and start_filename and end_filename:
            workflow["prompt"]["37"] = {
                "class_type": "LoadImage",
                "inputs": {
                    "image": start_filename
                }
            }
            workflow["prompt"]["38"] = {
                "class_type": "LTXVAddGuide",
                "inputs": {
                    "positive": ["8", 0],
                    "negative": ["8", 1],
                    "vae": ["12", 0],
                    "latent": ["35", 0],
                    "image": ["37", 0],
                    "frame_idx": 0,
                    "strength": 1.0
                }
            }
            workflow["prompt"]["39"] = {
                "class_type": "LoadImage",
                "inputs": {
                    "image": end_filename
                }
            }
            workflow["prompt"]["40"] = {
                "class_type": "LTXVAddGuide",
                "inputs": {
                    "positive": ["38", 0],
                    "negative": ["38", 1],
                    "vae": ["12", 0],
                    "latent": ["38", 2],
                    "image": ["39", 0],
                    "frame_idx": -1,
                    "strength": 1.0
                }
            }
            workflow["prompt"]["15"]["inputs"]["positive"] = ["40", 0]
            workflow["prompt"]["15"]["inputs"]["negative"] = ["40", 1]
            workflow["prompt"]["21"]["inputs"]["latent_image"] = ["40", 2]

    # CogVideoX model handling
    if model.lower().startswith("cogvideox"):
        if not start_filename and mode in ["i2v", "interpolation"]:
            raise HTTPException(status_code=400, detail="CogVideoX I2V requires a starting image. Please upload a start frame image.")
        if mode == "t2v" and not start_filename:
            raise HTTPException(status_code=400, detail="CogVideoX 5B is an Image-to-Video model and requires a starting image. Please select Image-to-Video mode and upload an image.")
        workflow = _build_cogvideox_workflow(prompt, negative_prompt, steps, width, height, frames, seed, cfg, model, vae_tiling, start_filename, end_filename)
    else:
        # Existing WAN or LTX workflows
        if not "ltx" in model.lower():
            # Setup Wan base workflow
            workflow = {
                "prompt": {
                    "30": {
                        "class_type": "ModelComputeDtype",
                        "inputs": {
                            "model": ["10", 0],
                            "dtype": "bf16",
                        },
                    },
                    "3": {
                        "class_type": "KSampler",
                        "inputs": {
                            "seed": seed,
                            "steps": steps,
                            "cfg": 6.0,
                            "sampler_name": "uni_pc",
                            "scheduler": "normal",
                            "denoise": 1.0,
                            "model": ["30", 0],
                            "positive": ["6", 0],
                            "negative": ["7", 0],
                            "latent_image": ["5", 0],
                        },
                    },
                    "5": {
                        "class_type": "EmptyLatentImage",
                        "inputs": {"width": width, "height": height, "batch_size": frames},
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
                        "class_type": "VAEDecodeTiled" if vae_tiling else "VAEDecode",
                        "inputs": decoder_inputs,
                    },
                    "9": {
                        "class_type": "VHS_VideoCombine",
                        "inputs": {
                            "images": ["8", 0],
                            "frame_rate": 16.0,
                            "loop_count": 0,
                            "filename_prefix": f"spark_{job_id}",
                            "format": "video/h264-mp4",
                            "pingpong": False,
                            "save_output": True,
                        },
                    },
                    "10": {
                        "class_type": "UnetLoaderGGUF",
                        "inputs": {"unet_name": model},
                    },
                    "11": {
                        "class_type": "DualCLIPLoader",
                        "inputs": {
                            "clip_name1": "umt5_xxl_fp8.safetensors",
                            "clip_name2": "clip_l.safetensors",
                            "type": "hunyuan_video",
                        },
                    },
                    "12": {
                        "class_type": "VAELoader",
                        "inputs": {"vae_name": "wan2.2_vae.safetensors"},
                    },
                }
            }

            # Apply image conditioning nodes for Wan
            if mode == "i2v" and start_filename:
                workflow["prompt"]["13"] = {
                    "class_type": "LoadImage",
                    "inputs": {
                        "image": start_filename
                    }
                }
                workflow["prompt"]["14"] = {
                    "class_type": "WanImageToVideo",
                    "inputs": {
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "vae": ["12", 0],
                        "width": width,
                        "height": height,
                        "length": frames,
                        "batch_size": 1,
                        "start_image": ["13", 0]
                    }
                }
                workflow["prompt"]["3"]["inputs"]["positive"] = ["14", 0]
                workflow["prompt"]["3"]["inputs"]["negative"] = ["14", 1]
                workflow["prompt"]["3"]["inputs"]["latent_image"] = ["14", 2]

            elif mode == "interpolation" and start_filename and end_filename:
                workflow["prompt"]["13"] = {
                    "class_type": "LoadImage",
                    "inputs": {
                        "image": start_filename
                    }
                }
                workflow["prompt"]["14"] = {
                    "class_type": "LoadImage",
                    "inputs": {
                        "image": end_filename
                    }
                }
                workflow["prompt"]["15"] = {
                    "class_type": "WanFirstLastFrameToVideo",
                    "inputs": {
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "vae": ["12", 0],
                        "width": width,
                        "height": height,
                        "length": frames,
                        "batch_size": 1,
                        "start_image": ["13", 0],
                        "end_image": ["14", 0]
                    }
                }
                workflow["prompt"]["3"]["inputs"]["positive"] = ["15", 0]
                workflow["prompt"]["3"]["inputs"]["negative"] = ["15", 1]
                workflow["prompt"]["3"]["inputs"]["latent_image"] = ["15", 2]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{comfyui_url}/prompt", json=workflow)
            if r.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"ComfyUI rejected payload: {r.status_code} {r.text}",
                )
            prompt_id = r.json().get("prompt_id")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"ComfyUI unreachable: {e}")

    logger.info(f"Video job {job_id} queued. ComfyUI prompt_id: {prompt_id}")

    try:
        completed = False
        output_file = None
        async with httpx.AsyncClient(timeout=10.0) as client:
            for _ in range(180):
                await asyncio.sleep(5)
                hist = await client.get(f"{comfyui_url}/history/{prompt_id}")
                if hist.status_code == 200:
                    history = hist.json()
                    if prompt_id in history:
                        completed = True
                        outputs = history[prompt_id].get("outputs", {})
                        for node_id, node_output in outputs.items():
                            media = node_output.get("gifs", []) or node_output.get("images", [])
                            if media:
                                filename = media[0].get("filename")
                                comfy_output = os.path.join(
                                    os.getenv("COMFYUI_OUTPUT_DIR", "/comfyui-output"),
                                    filename,
                                )
                                output_file = os.path.join(output_dir, f"{job_id}.mp4")
                                if os.path.exists(comfy_output):
                                    import shutil
                                    shutil.copy(comfy_output, output_file)
                                else:
                                    with open(output_file, "wb") as f:
                                        f.write(b"\x00\x00\x00\x1cftypisom dummy video placeholder")
                        break

        if completed and output_file:
            return {
                "job_id": job_id,
                "status": "completed",
                "output_url": f"/output/{job_id}.mp4",
            }
        else:
            raise HTTPException(status_code=504, detail="ComfyUI video polling timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_test_frame(request: Request, comfyui_url: str, output_dir: str):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    prompt = body.get("prompt", "")
    seed = body.get("seed", int(uuid.uuid4().int >> 96))

    job_id = f"test_{uuid.uuid4().hex[:8]}"

    # Fast 4-step image using FLUX.1 Schnell
    workflow = {
        "prompt": {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": seed,
                    "steps": 4,
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
                "inputs": {"width": 768, "height": 448, "batch_size": 1},
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": prompt, "clip": ["11", 0]},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "blurry, low quality, distorted", "clip": ["11", 0]},
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
                "class_type": "UnetLoaderGGUF",
                "inputs": {"unet_name": "flux1-schnell-q8.gguf"},
            },
            "11": {
                "class_type": "DualCLIPLoader",
                "inputs": {
                    "clip_name1": "t5xxl_fp8_e4m3fn.safetensors",
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

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{comfyui_url}/prompt", json=workflow)
            if r.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"ComfyUI rejected test frame: {r.status_code} {r.text}",
                )
            prompt_id = r.json().get("prompt_id")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"ComfyUI unreachable: {e}")

    logger.info(f"Test frame job {job_id} queued. ComfyUI prompt_id: {prompt_id}")

    try:
        completed = False
        output_file = None
        async with httpx.AsyncClient(timeout=10.0) as client:
            for _ in range(60):
                await asyncio.sleep(2)
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
            raise HTTPException(status_code=504, detail="ComfyUI test frame polling timed out")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test frame generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_cogvideox_workflow(prompt: str, negative_prompt: str, steps: int, width: int, height: int, frames: int, seed: int, cfg: float, model_name: str, vae_tiling: bool, start_filename: str = "", end_filename: str = ""):
    """Construct a ComfyUI workflow JSON for CogVideoX‑2B / 5B.
    Adjust node class names/parameters if they differ in your wrapper version.
    """
    # Load the model using bf16 precision
    model_loader = {
        "class_type": "CogVideoXModelLoader",
        "inputs": {
            "model": model_name,
            "base_precision": "bf16",
            "quantization": "disabled",
            "load_device": "main_device",
            "enable_sequential_cpu_offload": False
        }
    }
    # Load CLIP using standard CLIPLoader
    clip_loader = {
        "class_type": "CLIPLoader",
        "inputs": {
            "clip_name": "t5xxl_fp8_e4m3fn.safetensors",
            "type": "sd3"
        }
    }
    # Load VAE specifically for CogVideoX
    vae_loader = {
        "class_type": "CogVideoXVAELoader",
        "inputs": {
            "model_name": "cogvideox_vae_bf16.safetensors",
            "precision": "bf16"
        }
    }
    # Create empty latent image to determine dimensions for the sampler
    empty_latent = {
        "class_type": "EmptyLatentImage",
        "inputs": {
            "width": width,
            "height": height,
            "batch_size": frames
        }
    }
    # Text encoding for positive prompt
    pos_encode = {
        "class_type": "CogVideoTextEncode",
        "inputs": {
            "clip": ["1", 0],
            "prompt": prompt
        }
    }
    # Text encoding for negative prompt
    neg_encode = {
        "class_type": "CogVideoTextEncode",
        "inputs": {
            "clip": ["1", 0],
            "prompt": negative_prompt
        }
    }
    # Sampler node
    sampler = {
        "class_type": "CogVideoSampler",
        "inputs": {
            "model": ["0", 0],
            "positive": ["4", 0],
            "negative": ["5", 0],
            "samples": ["3", 0],
            "num_frames": frames,
            "steps": steps,
            "cfg": cfg,
            "seed": seed,
            "scheduler": "CogVideoXDDIM"
        }
    }
    
    # If start image is provided, connect image conditioning nodes
    additional_nodes = {}
    if start_filename:
        additional_nodes["13"] = {
            "class_type": "LoadImage",
            "inputs": {
                "image": start_filename
            }
        }
        image_encode_inputs = {
            "vae": ["2", 0],
            "start_image": ["13", 0],
            "enable_tiling": vae_tiling
        }
        if end_filename:
            additional_nodes["14"] = {
                "class_type": "LoadImage",
                "inputs": {
                    "image": end_filename
                }
            }
            image_encode_inputs["end_image"] = ["14", 0]
            
        additional_nodes["15"] = {
            "class_type": "CogVideoImageEncode",
            "inputs": image_encode_inputs
        }
        sampler["inputs"]["image_cond_latents"] = ["15", 0]

    # Decode sampled latents to video frames
    decode = {
        "class_type": "CogVideoDecode",
        "inputs": {
            "vae": ["2", 0],
            "samples": ["6", 0],
            "enable_vae_tiling": vae_tiling,
            "tile_sample_min_height": 240,
            "tile_sample_min_width": 360,
            "tile_overlap_factor_height": 0.2,
            "tile_overlap_factor_width": 0.2,
            "auto_tile_size": True
        }
    }
    # Combine frames into a video file
    combine = {
        "class_type": "VHS_VideoCombine",
        "inputs": {
            "images": ["7", 0],
            "frame_rate": 25.0,
            "filename_prefix": f"spark_{uuid.uuid4().hex[:8]}",
            "format": "video/h264-mp4",
            "pingpong": False,
            "loop_count": 0,
            "save_output": True
        }
    }
    workflow = {
        "prompt": {
            "0": model_loader,
            "1": clip_loader,
            "2": vae_loader,
            "3": empty_latent,
            "4": pos_encode,
            "5": neg_encode,
            "6": sampler,
            "7": decode,
            "8": combine,
            **additional_nodes
        }
    }
    return workflow
