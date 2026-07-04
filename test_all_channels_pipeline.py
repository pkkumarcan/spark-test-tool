#!/usr/bin/env python3
import os
import re
import sys
import time
import json
import httpx
import subprocess

BASE_URL = "http://localhost:5050"
CHANNELS_FILE = "/home/pkkumar/AGGY/spark-test-tool/app/data/channels_info.md"
OUTPUT_DIR = "/home/pkkumar/AGGY/spark-test-tool/output/test_channels"

# Map host output dir to container output dir
CONTAINER_OUTPUT_DIR = "/app/output/test_channels"

def parse_channels(filepath):
    channels = []
    current_channel = None
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        return []

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('###'):
                if current_channel:
                    channels.append(current_channel)
                name = line.split('.', 1)[-1].strip()
                current_channel = {"name": name}
            elif current_channel is not None:
                if "**Channel Code:**" in line:
                    match = re.search(r'`([^`]+)`', line)
                    if match:
                        current_channel["code"] = match.group(1).strip()
                elif "**Niche:**" in line:
                    current_channel["niche"] = line.split("**Niche:**")[-1].strip()
                elif "**Avatar:**" in line:
                    current_channel["avatar"] = line.split("**Avatar:**")[-1].strip()
                elif "**Mantra:**" in line:
                    mantra_part = line.split("**Mantra:**")[-1].strip()
                    # Strip quotes if present
                    if (mantra_part.startswith('"') and mantra_part.endswith('"')) or (mantra_part.startswith("'") and mantra_part.endswith("'")):
                        mantra_part = mantra_part[1:-1]
                    current_channel["mantra"] = mantra_part

    if current_channel:
        channels.append(current_channel)
    return [c for c in channels if "code" in c]

def check_gateway_alive():
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False

def generate_mock_video(channel_code):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    video_path = os.path.join(OUTPUT_DIR, f"{channel_code}_test.mp4")
    # Quick 2-second low-resolution mp4
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=indigo:s=640x360:d=2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        video_path
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return video_path
    except Exception as e:
        print(f"[{channel_code}] FFmpeg video generation failed: {e}")
        return None

def test_channel_pipeline(channel, available_models):
    code = channel["code"]
    name = channel["name"]
    niche = channel["niche"]
    avatar = channel["avatar"]
    mantra = channel["mantra"]

    print(f"\n--- Testing Pipeline for Channel: {name} ({code}) ---")
    results = {
        "channel": name,
        "code": code,
        "script_gen": "SKIP",
        "tts_gen": "SKIP",
        "video_stitch": "SKIP",
        "upload": "SKIP",
        "overall": "FAIL"
    }

    # Step 1: Script Gen via Gateway Ollama Endpoint
    print(f"[{code}] Step 1: Generating 1-sentence hook script...")
    model_to_use = "qwen3:8b"
    if available_models:
        if "qwen3:8b" in available_models:
            model_to_use = "qwen3:8b"
        elif "qwen3.6:27b" in available_models:
            model_to_use = "qwen3.6:27b"
        else:
            model_to_use = available_models[0]

    payload_script = {
        "model": model_to_use,
        "messages": [
            {
                "role": "system",
                "content": f"You are a script writer for {name}. Generate exactly one sentence for a YouTube video hook. Niche: {niche}. Avatar: {avatar}."
            },
            {
                "role": "user",
                "content": "Write the hook sentence."
            }
        ]
    }
    
    try:
        # Gateway chat endpoint is streaming (SSE). Handle it by yielding lines.
        script_text = ""
        with httpx.stream("POST", f"{BASE_URL}/api/text/chat", json=payload_script, timeout=30.0) as r:
            if r.status_code == 200:
                for line in r.iter_lines():
                    if line.startswith("data: "):
                        data_content = line[6:].strip()
                        try:
                            data_json = json.loads(data_content)
                            if "message" in data_json:
                                script_text += data_json["message"].get("content", "")
                            elif "response" in data_json:
                                script_text += data_json.get("response", "")
                        except Exception:
                            pass
                script_text = script_text.strip()
                print(f"  Generated Hook: \"{script_text[:100]}...\"")
                results["script_gen"] = "PASS" if script_text else "FAIL (empty)"
            else:
                print(f"  Warning: Script API returned status {r.status_code}. Content: {r.read()[:100]}")
                results["script_gen"] = f"FAIL (HTTP {r.status_code})"
    except Exception as e:
        print(f"  Error generating script: {e}")
        results["script_gen"] = f"FAIL ({str(e)[:50]})"

    # Step 2: Audio TTS via Gateway Endpoint
    print(f"[{code}] Step 2: Generating TTS for mantra: \"{mantra}\"...")
    payload_tts = {
        "text": mantra,
        "voice": "default"
    }
    try:
        r = httpx.post(f"{BASE_URL}/api/audio/speak", json=payload_tts, timeout=30.0)
        if r.status_code == 200:
            print("  TTS Voice synthesis succeeded.")
            results["tts_gen"] = "PASS"
        else:
            print(f"  Warning: TTS API returned status {r.status_code}")
            results["tts_gen"] = f"FAIL (HTTP {r.status_code})"
    except Exception as e:
        print(f"  Error generating TTS: {e}")
        results["tts_gen"] = f"FAIL ({str(e)[:50]})"

    # Step 3: Fast-stitching test video using FFmpeg
    print(f"[{code}] Step 3: Stitching lightweight mock video...")
    video_path = generate_mock_video(code)
    if video_path and os.path.exists(video_path):
        print(f"  Stitched video file created at {video_path}")
        results["video_stitch"] = "PASS"
    else:
        results["video_stitch"] = "FAIL"

    # Step 4: Publish upload draft via Gateway Endpoint
    print(f"[{code}] Step 4: Submitting upload draft...")
    if video_path:
        # Use container path mapping instead of host path mapping
        container_video_path = os.path.join(CONTAINER_OUTPUT_DIR, f"{code}_test.mp4")
        payload_upload = {
            "file_path": container_video_path,
            "metadata": {
                "title": f"Test Video - {name}",
                "description": f"Automated integration test for {name} ({code}). Mantra: {mantra}",
                "tags": [code, "integration-test"]
            }
        }
        try:
            r = httpx.post(f"{BASE_URL}/api/publish/upload", json=payload_upload, timeout=20.0)
            if r.status_code == 200 and r.json().get("status") == "success":
                video_id = r.json().get("video_id")
                print(f"  Upload successful. Mock Video ID: {video_id}")
                results["upload"] = "PASS"
            else:
                print(f"  Warning: Upload API returned {r.status_code}: {r.text}")
                results["upload"] = f"FAIL (HTTP {r.status_code})"
        except Exception as e:
            print(f"  Error during publish upload: {e}")
            results["upload"] = f"FAIL ({str(e)[:50]})"
    else:
        print("  Skipping upload step because mock video generation failed.")
        results["upload"] = "FAIL (No Video)"

    # Determine overall status
    if (results["script_gen"] == "PASS" and 
        results["tts_gen"] == "PASS" and 
        results["video_stitch"] == "PASS" and 
        results["upload"] == "PASS"):
        results["overall"] = "PASS"

    return results

def main():
    print("==================================================")
    print("      Spark Channels Pipeline Test Runner")
    print("==================================================")
    print()

    print("[1/3] Parsing channels_info.md...")
    channels = parse_channels(CHANNELS_FILE)
    print(f"  Found {len(channels)} configured channels.")
    if not channels:
        print("FAIL: No channels parsed.")
        sys.exit(1)

    print("[2/3] Verifying Spark Gateway is online...")
    if not check_gateway_alive():
        print(f"FAIL: Spark gateway is offline at {BASE_URL}. Run start.sh or docker compose first.")
        sys.exit(1)
    print("  OK: Gateway is responding")

    # Get available text models from gateway
    available_models = []
    try:
        r = httpx.get(f"{BASE_URL}/api/text/models", timeout=5.0)
        if r.status_code == 200:
            available_models = [m["name"] for m in r.json().get("models", [])]
            print(f"  Available Ollama Models: {available_models}")
    except Exception as e:
        print(f"  Warning: Could not fetch models list: {e}")

    print("\n[3/3] Starting pipeline tests across all channels...")
    all_results = []
    for c in channels:
        res = test_channel_pipeline(c, available_models)
        all_results.append(res)

    # Print Report Summary Table
    print("\n" + "="*50)
    print("               FINAL PIPELINE REPORT")
    print("="*50)
    print(f"| Code | Channel Name | Script | TTS | Video | Upload | Result |")
    print(f"|------|--------------|--------|-----|-------|--------|--------|")
    for r in all_results:
        res_indicator = "✅ PASS" if r["overall"] == "PASS" else "❌ FAIL"
        print(f"| {r['code']} | {r['channel'][:18]} | {r['script_gen']} | {r['tts_gen']} | {r['video_stitch']} | {r['upload']} | {res_indicator} |")

    # Write report file
    report_path = "/home/pkkumar/AGGY/spark-test-tool/output/channels_test_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Spark Media Factory Channels Pipeline Test Report\n\n")
        f.write(f"Executed at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Code | Channel Name | Script Gen | TTS Gen | Video Stitch | Pub Upload | Status |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in all_results:
            res_indicator = "**PASS**" if r["overall"] == "PASS" else "*FAIL*"
            f.write(f"| `{r['code']}` | {r['channel']} | {r['script_gen']} | {r['tts_gen']} | {r['video_stitch']} | {r['upload']} | {res_indicator} |\n")

    print(f"\nSaved markdown report to: {report_path}")

if __name__ == "__main__":
    main()
