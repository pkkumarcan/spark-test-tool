import os
import json
import httpx
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("spark.mcp.comfyui")

# Initialize FastMCP Server
mcp = FastMCP("ComfyUI")

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://host.docker.internal:8188")

@mcp.tool()
async def list_workflows() -> str:
    """List available ComfyUI workflow configurations in the workstation."""
    return json.dumps({
        "workflows": [
            "flux-image-generator", 
            "wan-video-generator", 
            "music-generator", 
            "3d-asset-generator"
        ]
    }, indent=2)

@mcp.tool()
async def trigger_render(workflow_name: str, positive_prompt: str) -> str:
    """Trigger a ComfyUI generation task for a positive text prompt. Returns the prompt ID."""
    # Construct a default workflow for Flux image generation
    payload = {
        "prompt": {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": 1337, "steps": 4, "cfg": 1.0, "sampler_name": "euler",
                    "scheduler": "normal", "denoise": 1.0, "model": ["10", 0],
                    "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]
                }
            },
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode", "inputs": {"text": positive_prompt, "clip": ["11", 0]}},
            "7": {"class_type": "CLIPTextEncode", "inputs": {"text": "blurry, low quality", "clip": ["11", 0]}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["12", 0]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": f"mcp_{workflow_name}", "images": ["8", 0]}},
            "10": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "flux1-schnell-q8.gguf"}},
            "11": {"class_type": "DualCLIPLoader", "inputs": {"clip_name1": "t5xxl_fp8_e4m3fn.safetensors", "clip_name2": "clip_l.safetensors", "type": "flux"}},
            "12": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}}
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{COMFYUI_URL}/prompt", json=payload)
            if r.status_code == 200:
                prompt_id = r.json().get("prompt_id")
                return f"Render triggered successfully. Prompt ID: {prompt_id}"
            return f"Error: ComfyUI rejected prompt submission with status {r.status_code}: {r.text}"
    except Exception as e:
        return f"Error connecting to ComfyUI API: {str(e)}"

@mcp.tool()
async def get_render_status(prompt_id: str) -> str:
    """Check status of a ComfyUI render job by prompt ID."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{COMFYUI_URL}/history/{prompt_id}")
            if r.status_code == 200:
                history = r.json()
                if prompt_id in history:
                    return f"Job Completed. Outputs: {json.dumps(history[prompt_id].get('outputs', {}))}"
                    
                # Check queue
                q_r = await client.get(f"{COMFYUI_URL}/queue")
                queue_info = q_r.json() if q_r.status_code == 200 else {}
                running = queue_info.get("queue_running", [])
                pending = queue_info.get("queue_pending", [])
                
                is_running = any(x[1] == prompt_id for x in running)
                is_pending = any(x[1] == prompt_id for x in pending)
                
                if is_running:
                    return "Job is currently rendering in ComfyUI."
                elif is_pending:
                    return "Job is queued and waiting for ComfyUI resources."
                return "Job is pending in ComfyUI queue."
            return f"Error fetching ComfyUI queue history: {r.status_code}"
    except Exception as e:
        return f"Error connecting to ComfyUI history API: {str(e)}"

if __name__ == "__main__":
    mcp.run()
