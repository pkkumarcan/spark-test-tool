#!/usr/bin/env python3
"""Convert weekly_pipeline.py output to AGGY dashboard format."""

import os
import json
import glob

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/home/pkkumar/spark-test-tool/output")

for job_dir in sorted(glob.glob(os.path.join(OUTPUT_DIR, "weekly_*"))):
    if not os.path.isdir(job_dir):
        continue
    
    job_id = os.path.basename(job_dir)
    brief_path = os.path.join(job_dir, "phase1_intelligence_brief.json")
    
    if os.path.exists(brief_path):
        continue
    
    meta_dir = os.path.join(job_dir, "metadata")
    if not os.path.isdir(meta_dir):
        continue
    
    topic_file = os.path.join(meta_dir, "topic.json")
    script_file = os.path.join(meta_dir, "script.json")
    channel_file = os.path.join(meta_dir, "channel.json")
    
    topic_data = {}
    script_data = {}
    channel_data = {}
    
    if os.path.exists(topic_file):
        with open(topic_file) as f:
            topic_data = json.load(f)
    if os.path.exists(script_file):
        with open(script_file) as f:
            script_data = json.load(f)
    if os.path.exists(channel_file):
        with open(channel_file) as f:
            channel_data = json.load(f)
    
    channel_id = channel_data.get("channel_id", "MLN")
    channel_name = channel_data.get("channel_name", "Unknown")
    
    scenes = script_data.get("scenes", [])
    sections = []
    for i, scene in enumerate(scenes):
        sections.append({
            "section_id": f"S{i+1:02d}",
            "label": scene.get("label", f"Scene {i+1}"),
            "narration": scene.get("narration", ""),
            "target_duration_seconds": scene.get("duration", 30),
            "visual_gen_prompt": {
                "scene_description": f"Scene: {scene.get('label', '')}",
                "comfyui_prompt": f"Cinematic {scene.get('label', '').lower()} scene, professional lighting, 16:9"
            },
            "audio_music_cue": {
                "mood": "engaging",
                "ace_step_prompt": "Professional documentary background music"
            },
            "voice_profile_id": "default"
        })
    
    brief = {
        "job_code": job_id,
        "status": "completed",
        "job_meta": {
            "input_topic": topic_data.get("topic_summary", topic_data.get("title", "")),
            "channel_niche": f"{channel_name} ({channel_id})"
        },
        "phase1_intelligence_brief": {
            "section_1_niche_trends": {
                "market_research_findings": [
                    topic_data.get("topic_summary", "Topic analysis pending."),
                    topic_data.get("hook", "Opening hook pending."),
                    topic_data.get("target_audience", "Target audience analysis pending.")
                ]
            },
            "section_1_market_research": {
                "what_was_researched": {"value": topic_data.get("topic_summary", ""), "rationale": "Channel-specific research"},
                "what_was_found": {"value": topic_data.get("hook", ""), "rationale": "Key findings"},
                "who_is_the_audience": {"demographics": topic_data.get("target_audience", ""), "psychographics": "Engaged viewers", "viewing_context": "Desktop/mobile", "rationale": "Target fit"},
                "when_and_where": {"timeliness": "Current", "market_context": "Active niche", "rationale": "Timely"},
                "why_this_topic": {"search_volume_signal": "High", "cpm_potential": "Strong", "competition_gap": "Moderate", "rationale": "Good potential"},
                "how_we_monetise": {"adsense_strategy": "Display ads", "sponsorship_angle": "Niche sponsors", "digital_product_tie_in": "Guide PDF", "affiliate_opportunities": "Related products", "rationale": "Multi-stream"}
            },
            "section_2_title_strategy": {
                "variants": topic_data.get("title_variants", [topic_data.get("title", "Untitled")])[:3]
            },
            "section_3_thumbnail_strategy": {
                "concepts": [{
                    "subject": topic_data.get("thumbnail_prompt", "Thumbnail concept"),
                    "text_overlay": topic_data.get("title", "")[:30],
                    "comfyui_generation_prompt": topic_data.get("thumbnail_prompt", "Professional YouTube thumbnail")
                }]
            },
            "section_4_master_script": {
                "content_mode": "narrator-led",
                "sections": sections
            },
            "section_6_seo_metadata": {
                "recommended_title": topic_data.get("title", "Untitled"),
                "alternate_titles_concept_angles": topic_data.get("title_variants", [])
            }
        }
    }
    
    with open(brief_path, "w") as f:
        json.dump(brief, f, indent=2)
    
    print(f"Created brief for {job_id}")

print("Done")
