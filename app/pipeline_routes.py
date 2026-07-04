import time
import uuid
import os
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse

router = APIRouter()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")

MOCK_BRIEF = {
    "job_code": "MLN-2026-W27-001",
    "status": "pending_approval",
    "job_meta": {
        "input_topic": "macroeconomics global finance crypto trends 2026",
        "channel_niche": "Finance & Wealth Preservation"
    },
    "phase1_intelligence_brief": {
        "section_1_niche_trends": {
            "market_research_findings": [
                "Central banks are accumulating gold at record pace, signaling de-dollarization concerns among sovereign wealth funds.",
                "Bitcoin ETF inflows surpassed $40B in Q1 2026, creating a new institutional adoption floor.",
                "The Fed's delayed rate cuts are compressing yield spreads, pushing retail investors toward alternative assets."
            ]
        },
        "section_1_market_research": {
            "what_was_researched": {"value": "Q3 2026 macro-finance landscape including central bank policy, crypto institutional flows, and retail sentiment shifts.", "rationale": "High CPM niche with evergreen search volume."},
            "what_was_found": {"value": "Strong convergence between gold accumulation, BTC ETF growth, and yield compression creating a unique investment window.", "rationale": "Timely and actionable for target audience."},
            "who_is_the_audience": {"demographics": "Males 28-55, household income $75K+, US/UK/AU", "psychographics": "Self-directed investors concerned about inflation and currency debasement", "viewing_context": "Desktop and mobile, evening hours", "rationale": "High engagement and CPM fit."},
            "when_and_where": {"timeliness": "Immediate — Fed meeting in 2 weeks", "market_context": "Gold at ATH, BTC consolidating near $120K", "rationale": "Peak search interest window."},
            "why_this_topic": {"search_volume_signal": "Very High — 'inflation hedge 2026' up 340% YoY", "cpm_potential": "$18-22 CPM range", "competition_gap": "Few quality explainers combining macro + crypto + gold", "rationale": "Underserved content gap with high monetisation."},
            "how_we_monetise": {"adsense_strategy": "Finance/brokerage display ads at premium CPM", "sponsorship_angle": "Gold IRA companies, crypto exchanges", "digital_product_tie_in": "Wealth preservation checklist PDF", "affiliate_opportunities": "Trading platform referral codes", "rationale": "Multi-stream yield maximisation."},
            "topic_shortlist": {
                "candidates": [
                    {"topic": "The 2026 Sovereign Debt Trap: How to Position", "ctr_score": 9.4, "shortlisted": True},
                    {"topic": "Why Central Banks Are Hoarding Gold Right Now", "ctr_score": 8.8, "shortlisted": False},
                    {"topic": "Bitcoin ETF Flows: What the Smart Money Knows", "ctr_score": 8.2, "shortlisted": False}
                ],
                "selection_rationale": "The sovereign debt trap angle combines all three macro themes (gold, crypto, rates) into a single compelling narrative with the highest predicted CTR."
            }
        },
        "section_2_title_strategy": {
            "ctr_framework_applied": "Curiosity gap + authority positioning",
            "variants": [
                {"rank": 1, "title": "The 2026 Sovereign Debt Trap: How to Position Before It's Too Late", "hook_type": "Fear/Urgency", "keyword_placement": "Front-loaded", "psychological_trigger": "Loss aversion", "thumbnail_compatibility": "Excellent", "rationale": "Creates immediate urgency with actionable promise."},
                {"rank": 2, "title": "Why Every Major Central Bank Is Quietly Buying Gold in 2026", "hook_type": "Conspiracy/Revelation", "keyword_placement": "Mid-sentence", "psychological_trigger": "Insider knowledge", "thumbnail_compatibility": "Good", "rationale": "Implies hidden information the viewer needs."},
                {"rank": 3, "title": "Your Savings Account Is Losing 8% Per Year — Here's the Fix", "hook_type": "Personal pain point", "keyword_placement": "Start", "psychological_trigger": "Direct financial pain", "thumbnail_compatibility": "Excellent", "rationale": "Makes it personal and immediately relevant."}
            ]
        },
        "section_3_thumbnail_strategy": {
            "visual_ctr_principles_applied": "Contrast focal point + emotional gaze following",
            "concepts": [
                {
                    "concept_id": "TH_01",
                    "recommended": True,
                    "subject": "Shattered golden dollar coin with Bitcoin glowing behind it",
                    "environment": "Dark navy gradient with subtle financial chart overlay",
                    "lighting": "Dramatic rim light from behind, cool blue ambient",
                    "colour_palette": "Gold, navy, electric blue",
                    "text_overlay": "THE DEBT TRAP",
                    "emotion_target": "Urgency and revelation",
                    "comfyui_generation_prompt": "A shattered golden US dollar coin in the foreground, fragments floating, behind it a glowing orange Bitcoin symbol emerging from darkness, dark navy gradient background with faint stock chart lines, dramatic rim lighting, photorealistic, 4K, cinematic composition, financial thriller aesthetic",
                    "comfyui_negative_prompt": "blurry, low quality, text artifacts, cartoon, anime",
                    "rationale": "High contrast between destruction (dollar) and emergence (BTC) creates visual tension that drives CTR."
                }
            ]
        },
        "section_4_master_script": {
            "content_mode": "narrator-led",
            "sections": [
                {
                    "section_id": "S01",
                    "label": "The Hook — Breaking the Illusion",
                    "narration": "What if I told you that the safest place you've been storing your money — your savings account — is actually the most dangerous place it can be? In 2026, the global financial system is quietly shifting beneath our feet, and most people won't notice until it's too late.",
                    "target_duration_seconds": 35,
                    "voice_profile_id": "Sterling (The Analyst)",
                    "visual_gen_prompt": {
                        "scene_description": "Camera slowly pushes in on a dimly lit desk with financial documents, a golden coin, and a glowing screen showing crypto charts.",
                        "comfyui_prompt": "Cinematic push-in shot of a dark mahogany desk with scattered financial documents, a single golden coin catching light, laptop screen showing green crypto charts, warm amber desk lamp, shallow depth of field, film grain, 4K cinematic"
                    },
                    "audio_music_cue": {"mood": "Tense anticipation", "ace_step_prompt": "Dark ambient suspense, low bass drone, subtle piano notes, building tension"},
                    "rationale": "Immediate personal stakes hook. The 'what if I told you' pattern has proven 9.2/10 CTR in finance niches."
                },
                {
                    "section_id": "S02",
                    "label": "The Macro Picture — Central Banks & Gold",
                    "narration": "Over the past 18 months, central banks worldwide have purchased more gold than at any point since 1971. China, India, Poland, Turkey — they're all quietly building reserves. Why? Because they see what's coming: a structural shift away from dollar-denominated debt.",
                    "target_duration_seconds": 45,
                    "voice_profile_id": "Sterling (The Analyst)",
                    "visual_gen_prompt": {
                        "scene_description": "Animated world map showing gold reserve accumulation arrows flowing from West to East, with rising bar charts.",
                        "comfyui_prompt": "Dark world map with glowing gold arrows showing trade flows, rising bar charts in amber and gold, data visualization style, clean modern infographic aesthetic, dark background, 4K"
                    },
                    "audio_music_cue": {"mood": "Authoritative revelation", "ace_step_prompt": "Cinematic orchestral swell, mid-tempo, brass undertones, investigative journalism feel"},
                    "rationale": "Builds authority through data. The central bank gold angle is the highest-searched subtopic in this niche."
                },
                {
                    "section_id": "S03",
                    "label": "The Crypto Convergence — Institutional Flows",
                    "narration": "Meanwhile, Bitcoin ETF inflows have crossed $40 billion this quarter alone. BlackRock, Fidelity, Ark — the institutions aren't just experimenting anymore. They're positioning. And when smart money moves this aggressively, it's not speculation — it's conviction.",
                    "target_duration_seconds": 40,
                    "voice_profile_id": "Sterling (The Analyst)",
                    "visual_gen_prompt": {
                        "scene_description": "Split screen showing institutional trading floor on left and Bitcoin price chart surging on right.",
                        "comfyui_prompt": "Split screen composition, left side modern trading floor with multiple screens showing financial data, right side dramatic Bitcoin price chart going vertical in green, dark cinematic lighting, professional financial photography style, 4K"
                    },
                    "audio_music_cue": {"mood": "Building momentum", "ace_step_prompt": "Electronic ambient with rising synth pads, tech-forward, progressive build, modern finance aesthetic"},
                    "rationale": "Bridges traditional finance audience to crypto. The ETF flow data provides concrete evidence."
                },
                {
                    "section_id": "S04",
                    "label": "The Yield Compression Problem",
                    "narration": "Here's what most people miss: the Fed's delayed rate cuts are creating a yield compression spiral. When your savings account pays 4% but real inflation runs at 8%, you're not earning — you're losing 4% every single year. That's not a savings account. That's a slow-motion robbery.",
                    "target_duration_seconds": 42,
                    "voice_profile_id": "Sterling (The Analyst)",
                    "visual_gen_prompt": {
                        "scene_description": "Animated gauge showing inflation rate overtaking savings yield, with red warning indicators.",
                        "comfyui_prompt": "Close-up of a financial gauge or speedometer, needle pointing to danger zone in red, 'INFLATION' label prominent, dark dramatic background, warning light aesthetic, 4K detail"
                    },
                    "audio_music_cue": {"mood": "Urgency and concern", "ace_step_prompt": "Minimal piano with ticking clock undertone, anxious but controlled, investigative mood"},
                    "rationale": "Makes the problem visceral and personal. The 'robbery' metaphor triggers loss aversion."
                },
                {
                    "section_id": "S05",
                    "label": "The Positioning Framework",
                    "narration": "So what does the smart money do? Three moves: First, allocate 10-15% to physical gold or gold ETFs as a sovereign risk hedge. Second, maintain a 5-8% Bitcoin allocation as asymmetric upside insurance. Third, shift short-term savings into Treasury bills or I-bonds that adjust for inflation. This isn't financial advice — it's pattern recognition.",
                    "target_duration_seconds": 50,
                    "voice_profile_id": "Sterling (The Analyst)",
                    "visual_gen_prompt": {
                        "scene_description": "Clean three-column infographic showing the three positioning strategies with icons.",
                        "comfyui_prompt": "Modern dark infographic with three columns, icons for gold bar, Bitcoin symbol, and Treasury bond, clean typography, navy and gold color scheme, professional financial presentation style, 4K"
                    },
                    "audio_music_cue": {"mood": "Confident and clear", "ace_step_prompt": "Clean ambient electronic, steady rhythm, authoritative yet approachable, solution-oriented"},
                    "rationale": "Actionable framework gives the viewer concrete next steps, increasing save/share rate."
                },
                {
                    "section_id": "S06",
                    "label": "Outro & CTA",
                    "narration": "The debt trap is real, but it's not inevitable. The people who see it coming are already positioning. If this breakdown helped you understand the macro picture, hit subscribe — we go deep on wealth preservation strategies every week. Drop a comment with your allocation strategy. See you in the next one.",
                    "target_duration_seconds": 25,
                    "voice_profile_id": "Sterling (The Analyst)",
                    "visual_gen_prompt": {
                        "scene_description": "Channel branding end card with subscribe button animation and next video thumbnail.",
                        "comfyui_prompt": "Clean dark end card with channel logo, subscribe button glow effect, two video thumbnail placeholders, modern minimal design, navy and gold accent colors, 4K"
                    },
                    "audio_music_cue": {"mood": "Warm resolution", "ace_step_prompt": "Uplifting ambient outro, gentle fade, positive resolution, clean electronic ending"},
                    "rationale": "Standard CTA with community engagement prompt to boost algorithm signals."
                }
            ]
        },
        "section_5_audio_strategy": {
            "narration_voice": "Sterling (The Analyst) — Deep, authoritative male voice with measured pacing",
            "background_music": "Dark ambient cinematic, transitioning to confident electronic in framework section",
            "sfx_cues": ["Coin shimmer S01", "Data whoosh S02", "Trading floor ambient S03"]
        },
        "section_6_seo_metadata": {
            "recommended_title": "The 2026 Sovereign Debt Trap: How to Position Before It's Too Late",
            "alternate_titles_concept_angles": [
                "Why Every Major Central Bank Is Quietly Buying Gold in 2026",
                "Your Savings Account Is Losing 8% Per Year — Here's the Fix",
                "The Global Financial Reset Nobody Is Talking About"
            ],
            "description": "Central banks are buying record gold, Bitcoin ETFs hit $40B inflows, and your savings account is losing to inflation. Here's how smart money is positioning for the 2026 sovereign debt trap.",
            "tags": ["macroeconomics", "gold investment", "bitcoin ETF", "inflation 2026", "wealth preservation", "federal reserve", "sovereign debt", "crypto institutional"],
            "hashtags": ["#MacroEconomics", "#GoldInvestment", "#Bitcoin2026", "#WealthPreservation"]
        }
    }
}


MOCK_JOBS = [
    {
        "job_id": "pipeline_mock001",
        "job_code": "MLN-2026-W27-001",
        "channel_id": "MLN",
        "topic": "macroeconomics global finance crypto trends 2026",
        "status": "pending_approval",
        "current_step": "B",
        "year_week": "2026-W27",
        "content_type": "flagship",
        "job_meta": {"channel_niche": "Finance & Wealth Preservation"},
        "updated_at": time.time()
    },
    {
        "job_id": "pipeline_mock002",
        "job_code": "BWA-2026-W27-001",
        "channel_id": "BWA",
        "topic": "applied AI automation n8n local LLM agent workflows",
        "status": "completed",
        "current_step": "H",
        "year_week": "2026-W27",
        "content_type": "daily",
        "job_meta": {"channel_niche": "AI Tech & Automation"},
        "updated_at": time.time() - 3600
    },
    {
        "job_id": "pipeline_mock003",
        "job_code": "PKP-2026-W26-003",
        "channel_id": "PKP",
        "topic": "biohacking longevity sleep optimization protocols",
        "status": "completed",
        "current_step": "H",
        "year_week": "2026-W26",
        "content_type": "flagship",
        "job_meta": {"channel_niche": "Biohacking & Longevity"},
        "updated_at": time.time() - 86400
    },
]


@router.get("/pipeline/jobs")
async def list_jobs(channel_id: str = None):
    jobs = MOCK_JOBS
    if channel_id:
        jobs = [j for j in jobs if j["channel_id"] == channel_id]
    return jobs


@router.post("/pipeline/run")
async def run_pipeline(request: Request):
    body = await request.json()
    job_id = f"pipeline_{uuid.uuid4().hex[:8]}"
    new_job = {
        "job_id": job_id,
        "job_code": f"{body.get('channel_id', 'MLN')}-2026-W27-{len(MOCK_JOBS)+1:03d}",
        "channel_id": body.get("channel_id", "MLN"),
        "topic": body.get("topic", "general trends"),
        "status": "pending_approval",
        "current_step": "B",
        "year_week": "2026-W27",
        "content_type": "flagship",
        "job_meta": {"channel_niche": "General"},
        "updated_at": time.time()
    }
    MOCK_JOBS.insert(0, new_job)
    return {"job_id": job_id}


@router.get("/pipeline/brief/{job_id}")
async def get_brief(job_id: str):
    brief = dict(MOCK_BRIEF)
    brief["status"] = "pending_approval"
    return brief


@router.get("/pipeline/status/{job_id}")
async def get_status(job_id: str):
    return {
        "channel_id": "MLN",
        "topic": "macroeconomics global finance crypto trends 2026",
        "status": "pending_approval",
        "current_step": "B",
        "steps": {
            "A": {"status": "passed", "msg": "Topic generation complete"},
            "B": {"status": "passed", "msg": "Script synthesis complete"},
            "C": {"status": "pending", "msg": "Awaiting approval"},
            "D": {"status": "pending", "msg": "Awaiting approval"},
            "E": {"status": "pending", "msg": "Queued"},
            "F": {"status": "pending", "msg": "Queued"},
            "G": {"status": "pending", "msg": "Queued"},
            "H": {"status": "pending", "msg": "Queued"},
            "QC": {"status": "pending", "msg": "Queued"}
        }
    }


@router.post("/pipeline/approve/{job_id}")
async def approve_pipeline(job_id: str, request: Request):
    body = await request.json()
    for job in MOCK_JOBS:
        if job["job_id"] == job_id:
            job["status"] = "processing"
            job["current_step"] = "C"
            break
    return {"ok": True, "message": "Phase 2 dispatch initiated"}


@router.post("/pipeline/reject/{job_id}")
async def reject_pipeline(job_id: str):
    for job in MOCK_JOBS:
        if job["job_id"] == job_id:
            job["status"] = "failed"
            break
    return {"ok": True, "message": "Pipeline rejected"}


@router.get("/pipeline/assets/{job_id}")
async def list_assets(job_id: str):
    return []


@router.post("/pipeline/regenerate-field")
async def regenerate_field(request: Request):
    body = await request.json()
    instruction = body.get("instruction", "")
    field_content = body.get("field_content", "")
    return {"result": f"[Regenerated per instruction: '{instruction}'] {field_content[:80]}..."}


@router.post("/pipeline/export")
async def export_pipeline(request: Request):
    body = await request.json()
    filename = body.get("filename", "export.md")
    content = body.get("content", "")
    job_id = body.get("job_id", "default")
    out_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)
    return {"ok": True, "path": filepath}


@router.get("/pipeline/download")
async def download_export(job_id: str = "", filename: str = ""):
    filepath = os.path.join(OUTPUT_DIR, job_id, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath, filename=filename)
    raise HTTPException(status_code=404, detail="Export file not found")


@router.get("/pipeline/topic/{job_id}")
async def get_topic(job_id: str):
    return {
        "winning_topic": "The 2026 Sovereign Debt Trap: How to Position",
        "title_variants": [
            "The 2026 Sovereign Debt Trap: How to Position Before It's Too Late",
            "Why Every Major Central Bank Is Quietly Buying Gold in 2026",
            "Your Savings Account Is Losing 8% Per Year — Here's the Fix"
        ],
        "thumbnail_concepts": [
            "Shattered golden dollar coin with Bitcoin glowing behind it",
            "Central bank vault door opening to reveal gold bars",
            "Inflation gauge needle in the red zone"
        ]
    }


@router.get("/pipeline/script/{job_id}")
async def get_script(job_id: str):
    return {
        "mode": "narrator-led",
        "sections": [
            {"section_id": "S01", "label": "The Hook", "narration": "What if I told you the safest place for your money is actually the most dangerous?", "target_duration_seconds": 35},
            {"section_id": "S02", "label": "Central Banks & Gold", "narration": "Central banks have purchased more gold than at any point since 1971.", "target_duration_seconds": 45},
            {"section_id": "S03", "label": "Crypto Convergence", "narration": "Bitcoin ETF inflows have crossed $40 billion this quarter alone.", "target_duration_seconds": 40},
            {"section_id": "S04", "label": "Yield Compression", "narration": "When your savings account pays 4% but real inflation runs at 8%, you're losing.", "target_duration_seconds": 42},
            {"section_id": "S05", "label": "Positioning Framework", "narration": "Three moves: gold allocation, Bitcoin insurance, and inflation-adjusted savings.", "target_duration_seconds": 50},
            {"section_id": "S06", "label": "Outro & CTA", "narration": "The debt trap is real, but it's not inevitable. Subscribe for weekly breakdowns.", "target_duration_seconds": 25}
        ]
    }


@router.post("/video/test-frame")
async def test_frame(request: Request):
    return {"url": "/static/placeholder_frame.png"}


@router.get("/research/files")
async def list_research_files():
    return {
        "files": [
            {"name": "consolidated_research_brief.md", "rel_path": "consolidated_research_brief.md", "word_count": 4820},
            {"name": "central_bank_gold_accumulation.md", "rel_path": "central_bank_gold_accumulation.md", "word_count": 2150},
            {"name": "bitcoin_etf_flows_q1_2026.md", "rel_path": "bitcoin_etf_flows_q1_2026.md", "word_count": 1890},
            {"name": "fed_rate_decision_impact.md", "rel_path": "fed_rate_decision_impact.md", "word_count": 1640},
            {"name": "retail_investor_sentiment.md", "rel_path": "retail_investor_sentiment.md", "word_count": 1320}
        ]
    }


@router.get("/research/file")
async def get_research_file(path: str = ""):
    content_map = {
        "consolidated_research_brief.md": "# Q3 2026 Executive Consolidated Brief\n\n## Macro-Finance Landscape\n\nThe convergence of central bank gold accumulation, institutional Bitcoin adoption, and yield compression creates a once-in-a-decade positioning opportunity.\n\n### Key Findings\n\n1. **Central Bank Gold**: Record purchases since 1971\n2. **BTC ETF Inflows**: $40B+ in Q1 2026\n3. **Yield Compression**: Real savings rates negative at -4%\n\n### Investment Implications\n\n- 10-15% gold allocation recommended\n- 5-8% BTC as asymmetric upside\n- Shift to T-bills or I-bonds for savings",
        "central_bank_gold_accumulation.md": "# Central Bank Gold Accumulation 2026\n\n## Overview\n\nCentral banks globally have purchased over 1,200 tonnes of gold in the past 18 months, the highest pace since the collapse of Bretton Woods.\n\n## Key Buyers\n\n- **China (PBOC)**: +400 tonnes\n- **India (RBI)**: +180 tonnes\n- **Poland (NBP)**: +120 tonnes\n- **Turkey (CBRT)**: +95 tonnes",
        "bitcoin_etf_flows_q1_2026.md": "# Bitcoin ETF Flows — Q1 2026\n\n## Summary\n\nTotal ETF inflows surpassed $40 billion, driven primarily by BlackRock's IBIT and Fidelity's FBTC.\n\n## Institutional Breakdown\n\n| Fund | Inflows |\n|------|----------|\n| IBIT | $18.2B |\n| FBTC | $12.4B |\n| ARKB | $4.8B |\n| Other | $4.6B |",
    }
    content = content_map.get(path, f"# {path}\n\nResearch content for {path}.\n\nThis is a stub document. Full content would be generated by the LLM research pipeline.")
    return {"content": content}


@router.post("/research/compile")
async def compile_research():
    return {"ok": True, "message": "Research brief compiled successfully"}


@router.post("/research/expand")
async def expand_research():
    return {"ok": True, "message": "Research files expanded to target word counts"}


@router.get("/assets")
async def list_all_assets():
    return []
