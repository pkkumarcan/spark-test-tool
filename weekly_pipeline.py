#!/usr/bin/env python3
"""Run one week's pipeline for all 12 channels — skip video generation."""

import os
import json
import time
import httpx
import asyncio
import subprocess
from pathlib import Path

BASE = "http://localhost:5050"
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/home/pkkumar/spark-test-tool/output")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
F5_TTS_URL = "http://localhost:8020"
WHISPER_URL = "http://localhost:8010"

CHANNELS = {
    "MLN": {"name": "Macro Lens", "topic": "macroeconomics global finance crypto trends 2026"},
    "RMR": {"name": "Roam Rich", "topic": "digital nomad geo-arbitrage relocation tax strategies"},
    "NHZ": {"name": "Next Horizon", "topic": "quantum computing commercial space race frontier science"},
    "PKP": {"name": "Peak Protocol", "topic": "biohacking longevity sleep optimization peak performance"},
    "STM": {"name": "Still Mind", "topic": "stoic philosophy mental resilience modern anxiety tools"},
    "ODA": {"name": "Odd Archive", "topic": "unexplained history scientific paradoxes strange facts"},
    "DFW": {"name": "Drift Wave", "topic": "lofi music coding study soundscapes deep work ambient"},
    "ISL": {"name": "Inner Scroll", "topic": "sacred Eastern texts vedic wisdom spiritual translation"},
    "BWA": {"name": "Build With AI", "topic": "applied AI automation n8n local LLM agent workflows"},
    "DKS": {"name": "Dark Shield", "topic": "cybersecurity digital privacy opsec data breach protection"},
    "CCL": {"name": "Case Closed", "topic": "high profile court trial legal strategy jury analysis"},
    "GDB": {"name": "Ground Brief", "topic": "geopolitics global trade supply chain policy briefings"},
}

MODEL = os.getenv("DEFAULT_LLM_MODEL", "qwen3:4b-instruct")


def log(ch, msg):
    print(f"  [{ch}] {msg}")


def ensure_dirs(job_id):
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(os.path.join(job_dir, "audio"), exist_ok=True)
    os.makedirs(os.path.join(job_dir, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(job_dir, "metadata"), exist_ok=True)
    return job_dir


def step_a_topic(channel_id, channel_info):
    """Generate topic + title variants via Ollama."""
    prompt = f"""You are a YouTube content strategist for the channel "{channel_info['name']}".
Niche: {channel_info['topic']}

Generate ONE flagship video topic for this week. Return ONLY valid JSON:
{{
  "title": "Video title (max 70 chars, curiosity-driven)",
  "topic_summary": "2-3 sentence summary of the video content",
  "hook": "Opening hook line for narration (1-2 sentences)",
  "target_audience": "Who this is for",
  "title_variants": ["Variant 1", "Variant 2", "Variant 3"],
  "thumbnail_prompt": "ComfyUI image generation prompt for thumbnail"
}}"""

    try:
        r = httpx.post(f"{OLLAMA_URL}/api/generate", json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.7, "num_predict": 512}
        }, timeout=60)
        raw = r.json().get("response", "")
        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(raw[json_start:json_end])
    except Exception as e:
        log(channel_id, f"Topic gen failed: {e}")

    return {
        "title": f"Deep Dive: {channel_info['topic'].split()[0].title()} in 2026",
        "topic_summary": f"Exploring {channel_info['topic']}",
        "hook": f"What most people get wrong about {channel_info['topic'].split()[0]}.",
        "target_audience": "General audience interested in " + channel_info["topic"].split()[0],
        "title_variants": [f"The Truth About {channel_info['topic'].split()[0].title()}"],
        "thumbnail_prompt": f"Professional YouTube thumbnail for {channel_info['topic']}"
    }


def step_b_script(channel_id, channel_info, topic_data):
    """Generate narration script via Ollama."""
    prompt = f"""You are a professional YouTube scriptwriter for "{channel_info['name']}".
Write a 3-4 minute narration script for: {topic_data['title']}

{topic_data.get('topic_summary', '')}

Return ONLY valid JSON with an array of scenes:
{{
  "scenes": [
    {{"label": "Hook", "narration": "opening narration...", "duration": 20}},
    {{"label": "Main Content", "narration": "core content...", "duration": 60}},
    {{"label": "Deep Dive", "narration": "deeper analysis...", "duration": 50}},
    {{"label": "Conclusion", "narration": "wrap up and CTA...", "duration": 25}}
  ]
}}
Keep total duration under 180 seconds. Write in an engaging, conversational tone."""

    try:
        r = httpx.post(f"{OLLAMA_URL}/api/generate", json={
            "model": MODEL, "prompt": prompt, "stream": False,
            "options": {"temperature": 0.8, "num_predict": 1024}
        }, timeout=90)
        raw = r.json().get("response", "")
        json_start = raw.find("{")
        json_end = raw.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            return json.loads(raw[json_start:json_end])
    except Exception as e:
        log(channel_id, f"Script gen failed: {e}")

    return {"scenes": [
        {"label": "Hook", "narration": topic_data.get("hook", "Welcome to this video."), "duration": 20},
        {"label": "Main Content", "narration": topic_data.get("topic_summary", "Today we explore an interesting topic."), "duration": 80},
        {"label": "Conclusion", "narration": "Thanks for watching. Subscribe for more.", "duration": 25},
    ]}


def step_c_audio(channel_id, job_id, script_data, job_dir):
    """Generate voiceover audio via F5-TTS for each scene. Falls back to ffmpeg silence."""
    audio_files = []
    scenes = script_data.get("scenes", [])

    for i, scene in enumerate(scenes):
        narration = scene.get("narration", "")
        duration = scene.get("duration", 30)
        if not narration or len(narration.strip()) < 10:
            continue

        audio_path = os.path.join(job_dir, "audio", f"scene_{i+1:02d}_{scene.get('label', 'unknown').replace(' ', '_').lower()}.mp3")

        # Try F5-TTS first
        try:
            r = httpx.post(f"{F5_TTS_URL}/synthesize", json={
                "text": narration,
                "voice": "default",
                "speed": 1.0
            }, timeout=120)

            if r.status_code == 200 and len(r.content) > 100:
                with open(audio_path, "wb") as f:
                    f.write(r.content)
                audio_files.append(audio_path)
                log(channel_id, f"  Audio scene {i+1}: {len(r.content)//1024}KB (F5-TTS)")
                continue
        except Exception:
            pass

        # Fallback: generate silent audio with ffmpeg
        try:
            subprocess.run([
                "ffmpeg", "-y", "-f", "lavfi", "-i",
                f"anullsrc=r=24000:cl=mono:d={duration}",
                "-t", str(duration), "-q:a", "9", audio_path
            ], capture_output=True, timeout=10)
            if os.path.exists(audio_path):
                audio_files.append(audio_path)
                log(channel_id, f"  Audio scene {i+1}: {duration}s silence (ffmpeg fallback)")
        except Exception as e:
            log(channel_id, f"  Audio scene {i+1} failed: {e}")

    return audio_files


def save_metadata(job_dir, channel_id, topic_data, script_data, audio_files):
    """Save all generated metadata to files."""
    with open(os.path.join(job_dir, "metadata", "topic.json"), "w") as f:
        json.dump(topic_data, f, indent=2)
    with open(os.path.join(job_dir, "metadata", "script.json"), "w") as f:
        json.dump(script_data, f, indent=2)
    with open(os.path.join(job_dir, "metadata", "channel.json"), "w") as f:
        json.dump({"channel_id": channel_id, "channel_name": CHANNELS[channel_id]["name"]}, f, indent=2)

    full_text = ""
    for scene in script_data.get("scenes", []):
        full_text += f"\n## {scene.get('label', 'Scene')}\n\n{scene.get('narration', '')}\n"
    with open(os.path.join(job_dir, "scripts", "narration.md"), "w") as f:
        f.write(f"# {topic_data.get('title', 'Untitled')}\n\n**Channel:** {CHANNELS[channel_id]['name']} ({channel_id})\n\n{full_text}")


async def run_all():
    print(f"\n{'='*60}")
    print(f"  SPARK MEDIA — Weekly Pipeline Run (12 Channels)")
    print(f"  Skipping: Video generation (D), Upscale (E), Stitch (F)")
    print(f"{'='*60}\n")

    results = {}

    for ch, info in CHANNELS.items():
        print(f"\n--- {ch}: {info['name']} ---")
        job_id = f"weekly_{ch}_{int(time.time())}"
        job_dir = ensure_dirs(job_id)
        log(ch, f"Job: {job_id}")

        # Step A: Topic Generation
        log(ch, "Step A: Generating topic...")
        topic_data = step_a_topic(ch, info)
        log(ch, f"  Title: {topic_data.get('title', 'N/A')}")

        # Step B: Script Synthesis
        log(ch, "Step B: Generating script...")
        script_data = step_b_script(ch, info, topic_data)
        scene_count = len(script_data.get("scenes", []))
        total_dur = sum(s.get("duration", 0) for s in script_data.get("scenes", []))
        log(ch, f"  Scenes: {scene_count}, Duration: ~{total_dur}s")

        # Step C: Audio Production
        log(ch, "Step C: Generating voiceover audio...")
        audio_files = step_c_audio(ch, job_id, script_data, job_dir)
        log(ch, f"  Audio files: {len(audio_files)}")

        # Save metadata
        save_metadata(job_dir, ch, topic_data, script_data, audio_files)

        # Step D/E/F: SKIPPED (video generation)
        log(ch, "Steps D/E/F: Skipped (video generation)")

        # Step G: Create publish metadata
        publish_data = {
            "title": topic_data.get("title", "Untitled"),
            "description": topic_data.get("topic_summary", ""),
            "tags": info["topic"].split(),
            "channel": ch,
            "status": "ready_for_review"
        }
        with open(os.path.join(job_dir, "metadata", "publish.json"), "w") as f:
            json.dump(publish_data, f, indent=2)
        log(ch, "Step G: Publish metadata created")

        # Step H: Create clip timestamps (placeholder)
        clip_data = {"clips": [{"start": 0, "end": 30, "label": "Hook"}]}
        with open(os.path.join(job_dir, "metadata", "clips.json"), "w") as f:
            json.dump(clip_data, f, indent=2)
        log(ch, "Step H: Clip metadata created")

        results[ch] = {
            "job_id": job_id,
            "title": topic_data.get("title", "N/A"),
            "scenes": scene_count,
            "audio_files": len(audio_files),
            "job_dir": job_dir,
        }
        log(ch, f"DONE")

    # Summary
    print(f"\n{'='*60}")
    print(f"  WEEKLY PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"  {'CH':<5} {'Channel':<18} {'Scenes':<8} {'Audio':<8} {'Title'}")
    print(f"  {'-'*5} {'-'*18} {'-'*8} {'-'*8} {'-'*30}")
    for ch, r in results.items():
        print(f"  {ch:<5} {CHANNELS[ch]['name']:<18} {r['scenes']:<8} {r['audio_files']:<8} {r['title'][:40]}")
    print(f"\n  Output: {OUTPUT_DIR}/")
    print(f"  Total jobs: {len(results)}")
    print(f"  Total audio files: {sum(r['audio_files'] for r in results.values())}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(run_all())
