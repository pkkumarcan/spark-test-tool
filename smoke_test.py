#!/usr/bin/env python3
"""Smoke test for LTX-2.3 video generation - verifies output is not black/empty."""

import sys
import time
import json
import httpx

COMFYUI_URL = "http://localhost:8188"
TEST_PROMPT = "A cat sitting on a windowsill looking outside at rain"
MIN_OUTPUT_SIZE_KB = 50


def check_comfyui_alive():
    try:
        r = httpx.get(f"{COMFYUI_URL}/system_stats", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False


def submit_ltx23_workflow():
    workflow = {
        "prompt": {
            "10": {
                "class_type": "UnetLoaderGGUF",
                "inputs": {
                    "unet_name": "ltx-2.3-22b-dev-Q4_K_M.gguf"
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
                    "width": 768,
                    "height": 448,
                    "length": 9,
                    "batch_size": 1
                }
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": TEST_PROMPT,
                    "clip": ["11", 0]
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": "blurry, low quality, distorted, black screen",
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
                    "steps": 8,
                    "max_shift": 2.05,
                    "base_shift": 0.95,
                    "stretch": True,
                    "terminal": 0.1
                }
            },
            "20": {
                "class_type": "RandomNoise",
                "inputs": {
                    "noise_seed": 42
                }
            },
            "21": {
                "class_type": "SamplerCustomAdvanced",
                "inputs": {
                    "model": ["10", 0],
                    "guiding": ["8", 0],
                    "sigmas": ["9", 0],
                    "noise": ["20", 0],
                    "latent_image": ["5", 0]
                }
            },
            "22": {
                "class_type": "LTXVTiledVAEDecode",
                "inputs": {
                    "samples": ["21", 0],
                    "vae": ["12", 0],
                    "tile_sample_min_height": 448,
                    "tile_sample_min_width": 768,
                    "tile_sample_min_num_frames": 9,
                    "tile_overlap_factor_height": 0.25,
                    "tile_overlap_factor_width": 0.25,
                    "tile_overlap_factor_time": 0.25,
                    "window_size": 448
                }
            },
            "23": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "smoke_ltx23",
                    "images": ["22", 0]
                }
            }
        }
    }

    r = httpx.post(f"{COMFYUI_URL}/prompt", json=workflow, timeout=30.0)
    if r.status_code != 200:
        print(f"FAIL: ComfyUI rejected workflow: {r.status_code} {r.text}")
        sys.exit(1)
    return r.json()["prompt_id"]


def poll_history(prompt_id, max_wait=900):
    start = time.time()
    while time.time() - start < max_wait:
        time.sleep(10)
        hist = httpx.get(f"{COMFYUI_URL}/history/{prompt_id}", timeout=10.0)
        if hist.status_code == 200:
            data = hist.json()
            if prompt_id in data:
                return data[prompt_id]
    return None


def check_output_size():
    import os, glob as g
    output_dir = "/home/pkkumar/spark-factory/ComfyUI/output"
    files = sorted(g.glob(os.path.join(output_dir, "smoke_ltx23_*")), key=os.path.getmtime, reverse=True)
    if not files:
        return None, 0
    f = files[0]
    size = os.path.getsize(f)
    return f, size


def main():
    print("=== LTX-2.3 Video Generation Smoke Test ===")
    print()

    print("[1/4] Checking ComfyUI is alive...")
    if not check_comfyui_alive():
        print("FAIL: ComfyUI is not responding at", COMFYUI_URL)
        sys.exit(1)
    print("  OK: ComfyUI is online")

    print("[2/4] Submitting LTX-2.3 workflow (9 frames, 768x448)...")
    try:
        prompt_id = submit_ltx23_workflow()
        print(f"  OK: prompt_id = {prompt_id}")
    except Exception as e:
        print(f"FAIL: Could not submit workflow: {e}")
        sys.exit(1)

    print(f"[3/4] Waiting for completion (up to 15 min)...")
    result = poll_history(prompt_id)
    if result is None:
        print("FAIL: Timed out waiting for ComfyUI to complete")
        sys.exit(1)

    status = result.get("status", {})
    if status.get("status_str") == "error":
        msgs = status.get("messages", [])
        for m in msgs:
            if isinstance(m, list) and len(m) > 1 and isinstance(m[1], dict):
                err = m[1].get("exception_message", "")
                if err:
                    print(f"FAIL: ComfyUI error: {err[:300]}")
                    sys.exit(1)
        print(f"FAIL: ComfyUI reported error")
        sys.exit(1)
    print("  OK: Workflow completed")

    print("[4/4] Checking output file size...")
    filepath, size = check_output_size()
    if filepath is None:
        print("FAIL: No output image found")
        sys.exit(1)

    size_kb = size / 1024
    print(f"  File: {filepath}")
    print(f"  Size: {size_kb:.1f} KB")

    if size_kb < 9:
        print(f"FAIL: File is only {size_kb:.1f} KB - likely a black screen")
        sys.exit(1)
    elif size_kb < MIN_OUTPUT_SIZE_KB:
        print(f"WARN: File is small ({size_kb:.1f} KB < {MIN_OUTPUT_SIZE_KB} KB)")
        print("  PASS with warning")
    else:
        print(f"  PASS: Output is {size_kb:.1f} KB (above {MIN_OUTPUT_SIZE_KB} KB threshold)")

    print()
    print("=== RESULT: ALL CHECKS PASSED ===")


if __name__ == "__main__":
    main()
