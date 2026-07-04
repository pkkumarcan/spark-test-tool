# X00 Network — Brand Channel Manifest & Pipeline v2.0

> 12-channel content network built for multi-stream income: AdSense, sponsorships, and digital products.
> All channels are designed for faceless, voiceover-led production optimised for YouTube and short-form social.
> **Scope:** Full-cycle automated content production for all 12 X71 network channels.
> **Modes:** Supports both `narrator-led` (single voiceover monologue) and `dialogue-led` (multi-character script) workflows.
> **Agent Rule:** Every step must complete and pass its validation gate before the next step begins. On any failure, halt and return a structured error report — never skip or auto-proceed past a failed gate.

---

## Pipeline Overview

```
A → B → [HUMAN CHECKPOINT] → C → D → E → F → G → H
```

| Step | Name | Mode | Gate Required |
|------|------|------|---------------|
| A | Idea & Topic Generation | Auto | CTR score ≥ threshold |
| B | Script Writing & QA | Auto | All QA checks pass |
| — | Human Checkpoint | Manual | Human approval token |
| C | Voiceover & Audio Production | Auto | Voice fingerprint match |
| D | Visual Generation | Auto | Style lock validation |
| E | Post-Processing & Upscaling | Auto | 4K artifact-free verification |
| F | Final Editing & Assembly | Auto | Sync offset < 80ms |
| G | Long-Form Publishing Package | Auto | Metadata completeness check |
| H | Short-Form Clips Pipeline | Auto | Per-platform spec validation |

---

## Global Constants (inject at every step)

The agent must load and attach the following context block at the start of each step:

```json
{
  "channel_id": "<C1–C12>",
  "channel_name": "<e.g. Macro Lens>",
  "channel_handle": "<e.g. @MacroLens>",
  "content_mode": "<narrator-led | dialogue-led>",
  "target_duration_seconds": "<300–1800>",
  "target_platform": "youtube",
  "style_card_path": "/channels/<channel_id>/style_card.json",
  "voice_profile_path": "/channels/<channel_id>/voice_profile.json",
  "rag_namespace": "<channel_id>",
  "output_root": "/output/<channel_id>/<job_id>/"
}
```

---

## Step A — Idea & Topic Generation

**Objective:** Identify and select the single best video topic for the current production cycle, validated for both audience demand and thumbnail CTR potential.

### A1 — Trend Research

**Action:**
- Call `/api/research/generate` with the channel niche keywords from the channel's style card.
- Fetch active search trends, news headlines, and rising queries from the past 48 hours.
- Return a raw list of 10–15 candidate topics.

**Output:** `a1_raw_topics.json` — list of topic strings with source URLs and trend velocity scores.

**Failure condition:** If fewer than 5 topics are returned, retry once. If still under 5, halt and flag for manual topic injection.

---

### A2 — Context Matching via RAG

**Action:**
- Call `/api/rag/query` with `namespace = channel_id`.
- Query the Qdrant RAG database using each candidate topic as a query string.
- Retrieve for each topic: channel persona rules, tone guidelines, previously covered topics (deduplication), audience profile, and banned subject list.

**Output:** `a2_context_matches.json` — each candidate topic annotated with RAG match score, persona fit rating, and deduplication flag.

**Failure condition:** If RAG returns zero results for a topic, mark it as `unvalidated` — do not discard, but flag for lower priority.

---

### A3 — CTR Pre-Scoring & Topic Selection

**Action:**
- For each validated candidate topic, generate a CTR pre-score (0–10) based on the following weighted criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Curiosity gap | 30% | Does the topic naturally produce a "you won't believe" or "most people don't know" angle? |
| Thumbnail visualisability | 25% | Can a high-contrast, single-subject thumbnail be designed for it? |
| Title hook strength | 25% | Does it support a title with a number, a contrarian claim, or a specific promise? |
| Niche relevance | 20% | Does it match the channel's core subject and audience profile from RAG? |

- Rank all topics by CTR pre-score.
- Select the top-scoring topic as the **winning concept**.
- generate 3 title variants and 2 thumbnail concept descriptions for the winning topic.

**Output:** `a3_selected_topic.json`
```json
{
  "winning_topic": "<topic string>",
  "ctr_score": 8.4,
  "title_variants": ["<title 1>", "<title 2>", "<title 3>"],
  "thumbnail_concepts": ["<concept 1>", "<concept 2>"],
  "rejected_topics": ["<topic>", "..."]
}
```

**Gate — A pass condition:** CTR pre-score of winning topic must be ≥ 7.0. If no topic scores ≥ 7.0, return all scored topics and halt for human selection.

---

## Step B — Script Writing & Generation

**Objective:** Produce a complete, QA-validated script ready for voiceover synthesis and visual mapping, with a verified opening hook.

### B1 — Master Script Generation

**Action:**
- Load `a3_selected_topic.json` and the channel style card.
- Generate the full master script according to `content_mode`:

**If `narrator-led`:**
```json
{
  "mode": "narrator-led",
  "sections": [
    {
      "section_id": "S01",
      "label": "hook",
      "narration": "<opening 30-second hook text>",
      "target_duration_seconds": 30
    },
    {
      "section_id": "S02",
      "label": "intro",
      "narration": "<channel intro and topic framing>",
      "target_duration_seconds": 45
    },
    {
      "section_id": "S03–SXX",
      "label": "body",
      "narration": "<main content segments>",
      "target_duration_seconds": "<variable>"
    },
    {
      "section_id": "SXX",
      "label": "cta",
      "narration": "<call to action and outro>",
      "target_duration_seconds": 30
    }
  ]
}
```

**If `dialogue-led`:**
```json
{
  "mode": "dialogue-led",
  "characters": [
    { "character_id": "C1", "name": "<name>", "voice_profile": "<profile_id>" }
  ],
  "sections": [
    {
      "section_id": "S01",
      "label": "hook",
      "dialogues": [
        { "character_id": "C1", "line": "<spoken line>", "emotion": "neutral" }
      ]
    }
  ]
}
```

**Output:** `b1_master_script.json`

**Failure condition:** If total estimated word count falls below minimum for target duration (calculated at 140 words/minute), regenerate with explicit length instruction. Maximum 2 retries before halting.

---

### B2 — Hook Audit

**Action:**
- Isolate the `hook` section (first 30 seconds / first ~70 words).
- Score the hook against the following checklist — every item is mandatory:

| Check | Pass Condition |
|-------|---------------|
| Urgency signal | First sentence creates immediate stakes ("By the end of this video...", "Most people get this completely wrong...") |
| Specific promise | A concrete payoff is stated within the first 3 sentences |
| No preamble | Hook does not begin with channel intro, greetings, or filler ("Hey guys, welcome back...") |
| Pattern interrupt | Opening uses a surprising fact, counter-intuitive claim, or direct question |
| Viewer benefit | The viewer understands what they will gain within 20 words |

- Return a pass/fail per check with a brief reason.
- If 4 or 5 checks pass, hook is approved.
- If 3 or fewer pass, regenerate the hook section only and re-audit. Maximum 3 regeneration attempts.

**Output:** `b2_hook_audit.json`

**Failure condition:** If hook fails after 3 attempts, halt and return all attempts for human review.

---

### B3 — Script Partitioning

**Action:**
- Split `b1_master_script.json` into two parallel output packs:

**Voiceover pack** — for Step C:
- Extract all narration text or dialogue lines in sequence order.
- Annotate each block with: `section_id`, `character_id` (if dialogue-led), `estimated_duration_seconds`, `emotion_tag`.

**Visual pack** — for Step D:
- For each section, generate a visual prompt describing the scene, mood, colour palette, camera framing, and any on-screen text overlays.
- Visual prompts must reference the channel's style card (art style, colour palette, banned visual elements).

**Output:**
- `b3_voiceover_pack.json`
- `b3_visual_pack.json`

---

### B4 — Script Compliance & QA

**Action:**
- Run the following automated checks against `b1_master_script.json` and `b3_voiceover_pack.json`:

| Check | Rule |
|-------|------|
| Total word count | Must be within ±10% of target word count (target_duration_seconds ÷ 60 × 140) |
| Reading pace | No single section exceeds 160 words/minute |
| Section balance | Hook ≤ 15% of total, CTA ≤ 10% of total, body ≥ 60% of total |
| Tone alignment | Script tone must match channel tone tag from style card (analytical / aspirational / calm / urgent / dramatic) |
| Banned terms | Zero matches against channel banned terms list from RAG |
| Visual prompt coverage | Every script section has a corresponding visual prompt in `b3_visual_pack.json` |

**Output:** `b4_qa_report.json` — pass/fail per check with line references for any failures.

**Gate — B pass condition:** All 6 checks must pass. Any failure halts pipeline and returns `b4_qa_report.json` with specific failure reasons.

---

## HUMAN CHECKPOINT

**Trigger:** Automatic — fires after B4 gate passes.

**Agent action:**
- Package and deliver to the human review queue:
  - `a3_selected_topic.json`
  - `b1_master_script.json`
  - `b2_hook_audit.json`
  - `b4_qa_report.json`
- Pause pipeline and wait for a human approval token.

**Human reviewer actions:**
- Read the master script in full.
- Optionally edit narration text directly (edits are re-validated through B4 before pipeline resumes).
- Issue one of: `APPROVE`, `REVISE:<instruction>`, or `REJECT:<reason>`.

**On `APPROVE`:** Pipeline resumes at Step C.
**On `REVISE`:** Agent applies the instruction, reruns B1→B4, and returns to the checkpoint.
**On `REJECT`:** Pipeline terminates. Job is logged as rejected. A new job must be started from Step A.

**Timeout:** If no human response is received within 24 hours, send a reminder. If no response within 48 hours, auto-escalate to channel manager.

---

## Step C — Voiceover & Audio Production

**Objective:** Produce a fully mixed, quality-verified audio master track — voice narration blended with background music — ready for video sync.

### C1 — Voiceover TTS Synthesis

**Action:**
- Load `b3_voiceover_pack.json` and the channel's `voice_profile.json`.
- For each voiceover block, call `/api/audio/speak` with:
  - `text`: narration or dialogue line
  - `voice_id`: from voice profile (per character if dialogue-led)
  - `emotion`: from emotion tag
  - `speed`: from voice profile baseline
  - `format`: WAV, 48kHz, 24-bit

**If dialogue-led:** Each character's lines are synthesised separately using their assigned voice profile. Maintain strict section and line ordering.

**Output:** `/output/<job_id>/audio/voice/` — individual WAV files named `S01_C1_line01.wav` etc.

**Failure condition:** If any TTS call returns an error or produces a file shorter than 80% of estimated duration, retry once. Log all retries.

---

### C2 — Voice Consistency QA

**Action:**
- Load the channel's reference voice fingerprint from `voice_profile.json` (pre-recorded reference sample per channel).
- For each synthesised WAV file, compare:

| Check | Rule |
|-------|------|
| Pitch drift | Fundamental frequency must be within ±5% of reference |
| Pace consistency | Words per minute must be within ±8% of voice profile target pace |
| Silence padding | Leading silence ≤ 100ms, trailing silence ≤ 200ms |
| Clipping | Peak amplitude must not exceed -1.0 dBFS |
| Noise floor | Background noise must be below -50 dBFS |

- Any file failing a check is flagged and re-synthesised once.
- If re-synthesis still fails, halt and log the specific file and failure reason.

**Output:** `c2_voice_qa_report.json`

**Gate — C2 pass condition:** All voice files pass all 5 checks.

---

### C3 — AI Music Generation

**Action:**
- Load the channel's music profile from the style card: mood tag, tempo range (BPM), instrumentation palette, and energy curve (e.g. low intro → builds mid → eases outro).
- Call `/api/music/generate` (ACE-Step via ComfyUI) with these parameters.
- Alternatively, if a matching asset exists in the local library at `/assets/music/<channel_id>/`, select the closest match and skip generation.
- Target output duration: `target_duration_seconds + 30` seconds (extra tail for fade).

**Output:** `/output/<job_id>/audio/music/bg_music.wav`

**Failure condition:** If generation fails, fall back to local library. If local library has no match, halt and request manual music selection.

---

### C4 — Audio Mixing & Levelling

**Action:**
- Concatenate all voice WAV files in section order using FFmpeg.
- Between dialogue lines (dialogue-led mode only): insert character-specific pause durations from voice profile.
- Apply the following FFmpeg processing chain in order:

```
1. Noise gate on voice track (threshold: -40 dBFS)
2. Normalise voice track to -16 LUFS integrated loudness
3. Duck background music to -22 dBFS under voice (sidechain: -10 dB reduction when voice present)
4. Music fade-in: 3 seconds at start
5. Music fade-out: 5 seconds at end
6. Final mix normalisation to -14 LUFS (YouTube standard)
7. Export stereo AAC 320kbps + WAV master
```

**Output:**
- `/output/<job_id>/audio/voice_master.wav`
- `/output/<job_id>/audio/mix_master.wav`
- `/output/<job_id>/audio/mix_master.aac`

**Failure condition:** If final LUFS is outside -13 to -15 range after processing, flag for manual level adjustment.

---

## Step D — Visual Generation

**Objective:** Produce all visual assets — keyframes, scene images, and animated video blocks — locked to the channel's style card to ensure visual consistency across all episodes.

### D0 — Style Lock Validation (pre-generation gate)

**Action — runs before any visual generation:**
- Load the channel's `style_card.json`.
- Confirm the following fields are present and non-empty:

| Field | Description |
|-------|-------------|
| `comfyui_checkpoint` | Specific model checkpoint filename |
| `lora_weights` | List of LoRA files and strengths |
| `colour_palette` | Hex codes for primary, secondary, accent |
| `lighting_direction` | e.g. "top-left rim light, cool tone" |
| `aspect_ratio` | "16:9" for long-form |
| `negative_prompt_base` | Global negative prompt for the channel |
| `banned_visual_elements` | List of disallowed subjects or styles |

**Gate — D0 pass condition:** All fields present. If any field is missing, halt immediately and request style card completion before visual generation begins. Do not generate a single image without a complete style card.

---

### D1 — Keyframe & Storyboard Generation

**Action:**
- Load `b3_visual_pack.json`.
- For each section's visual prompt, inject the style card parameters and call ComfyUI (`/api/image/generate`) to render:
  - 1 primary keyframe per section (main scene)
  - 1 alternate keyframe per section (fallback if primary fails QC)
- All prompts must include: `positive_prompt = visual_pack_prompt + style_card_base_prompt`, `negative_prompt = style_card_negative_prompt_base`, `checkpoint = style_card_comfyui_checkpoint`, `lora_weights = style_card_lora_weights`.

**Output:** `/output/<job_id>/visuals/keyframes/` — named `S01_primary.png`, `S01_alt.png` etc.

---

### D2 — Image Quality Control

**Action:**
- For every generated keyframe, run automated checks:

| Check | Rule |
|-------|------|
| Resolution | Must match target aspect ratio within 2px tolerance |
| Artefact detection | No visible generation artefacts (checkerboard, half-rendered faces, double exposures) |
| Style drift | CLIP embedding cosine similarity to channel reference image ≥ 0.75 |
| Banned elements | Zero matches against `banned_visual_elements` list from style card |

- If primary keyframe fails any check, promote the alternate.
- If both fail, regenerate with a simplified prompt. Maximum 2 regeneration attempts per section.
- Log all failures and regenerations.

**Output:** `d2_image_qc_report.json`

**Gate — D2 pass condition:** Every script section has at least one approved keyframe before proceeding to animation.

---

### D3 — Text-to-Video / Image-to-Video Animation

**Action:**
- Animate each approved keyframe into a video block using Wan 2.2 / LTX-Video on Node A.
- Animation parameters per section: duration = `section_estimated_duration_seconds`, motion strength = from style card (`low / medium / high`), camera movement = from visual pack prompt.
- For sections flagged as `static` in the visual pack (e.g. text-heavy explainer sections), use a subtle parallax or Ken Burns effect rather than full motion generation.

**Output:** `/output/<job_id>/visuals/video_blocks/` — named `S01_video.mp4` etc. at target resolution (pre-upscale).

**Failure condition:** Any video block shorter than 90% of target section duration must be regenerated. Log failures.

---

## Step E — Post-Processing & Upscaling

**Objective:** Upscale all raw video blocks to 4K, recover detail, interpolate frame rate, and verify output quality before assembly.

### E1 — Topaz Service Dispatch

**Action:**
- For each video block in `/output/<job_id>/visuals/video_blocks/`:
  - POST to Node B Topaz service at `http://10.0.0.162:5060/run`
  - Payload: `{ "input_path": "<block_path>", "models": ["Proteus", "Chronos"], "target_resolution": "3840x2160", "target_fps": 60 }`
- Dispatch all blocks in parallel where Node B capacity allows.
- Track job IDs returned by Topaz for polling.

**Output:** Topaz job ID list in `e1_dispatch_manifest.json`

---

### E2 — Model Application & Polling

**Action:**
- Poll Topaz job statuses every 60 seconds.
- Proteus model: detail recovery and sharpening pass.
- Chronos model: motion smoothing and frame rate interpolation to 60fps.
- On each job completion, retrieve output file and store in `/output/<job_id>/visuals/upscaled/`.

**Failure condition:** If a Topaz job fails or times out after 30 minutes, retry once. If second attempt fails, flag the block for manual upscaling or bypass with original resolution and log the exception.

---

### E3 — Polish Verification

**Action:**
- For every upscaled block, verify:

| Check | Rule |
|-------|------|
| Resolution | Exactly 3840×2160 |
| Frame rate | Exactly 60fps |
| Duration match | Within 0.5 seconds of original block duration |
| Artefact scan | No blocking, ghosting, or motion artefacts visible at 1:1 pixel review |
| File integrity | File is not corrupt and is readable by FFmpeg probe |

**Output:** `e3_polish_report.json`

**Gate — E3 pass condition:** All blocks pass all checks. Failed blocks must be resolved (retry or manual) before assembly begins.

---

## Step F — Final Editing & Assembly

**Objective:** Stitch all video and audio assets into a single broadcast-ready master file with subtitles, chapter markers, and end screen overlays burned in.

### F1 — Chapter Marker Generation

**Action:**
- Load `b1_master_script.json` section list with estimated durations.
- Calculate cumulative timestamps for each section boundary.
- Generate a chapters file in YouTube format:

```
00:00 Introduction
00:45 [Section 2 label]
03:20 [Section 3 label]
...
```

- Chapter labels must be derived from section labels in the master script — not generic ("Part 1", "Part 2").
- Minimum chapter length: 30 seconds. Merge short sections with adjacent sections if needed.

**Output:** `f1_chapter_markers.txt`

---

### F2 — Timeline Stitching

**Action:**
- Assemble the full video timeline using FFmpeg in this exact order:

```
1. Channel intro bumper (from /assets/brand/<channel_id>/intro.mp4) — max 5 seconds
2. Main content blocks (S01 through SXX in order)
3. CTA segment (from script CTA section video block)
4. End screen overlay (from /assets/brand/<channel_id>/endscreen.mp4) — 20 seconds
5. Channel outro bumper (from /assets/brand/<channel_id>/outro.mp4) — max 3 seconds
```

- All transitions: cross-dissolve, 12 frames (0.2 seconds at 60fps).
- All assets must be 3840×2160 60fps before stitching. Flag and halt if any asset does not match.

**Output:** `/output/<job_id>/final/video_raw.mp4`

---

### F3 — Audio/Video Sync

**Action:**
- Merge `mix_master.wav` with `video_raw.mp4` using FFmpeg.
- Measure A/V sync offset using waveform alignment between TTS peaks and any on-screen mouth movement (if applicable in dialogue-led mode).
- Acceptable sync offset: < 80ms.
- If offset ≥ 80ms, apply a manual audio delay/advance correction and re-measure.

**Output:** `/output/<job_id>/final/video_synced.mp4`

**Gate — F3 pass condition:** Sync offset < 80ms.

---

### F4 — Subtitle Burn-In

**Action:**
- Send `mix_master.wav` (voice track only, not the full mix) to `/api/audio/transcribe` (Whisper).
- Generate `.srt` subtitle file from transcription output.
- Validate SRT: check that subtitle timing aligns with voice WAV timing within 200ms per cue.
- Apply subtitle style from style card:
  - Font: channel-specified font from style card
  - Position: lower third, 8% from bottom
  - Background: semi-transparent pill behind each line
  - Max characters per line: 42
- Hardcode subtitle overlay onto `video_synced.mp4` using FFmpeg.

**Output:**
- `/output/<job_id>/final/subtitles.srt`
- `/output/<job_id>/final/video_final.mp4`

---

### F5 — Final Master Verification

**Action:**
- Run a final automated check on `video_final.mp4`:

| Check | Rule |
|-------|------|
| Resolution | 3840×2160 |
| Frame rate | 60fps |
| Duration | Within ±5 seconds of target |
| Audio levels | -14 LUFS integrated, peak < -1.0 dBFS |
| Subtitle presence | Subtitles visible in first and last 30 seconds |
| End screen present | End screen asset detectable in final 20 seconds |
| File size | < 20GB (YouTube upload limit) |

**Output:** `f5_final_verification.json`

**Gate — F5 pass condition:** All checks pass. Any failure halts delivery and returns specific failure detail.

---

## Step G — Long-Form Publishing Package

**Objective:** Generate a complete, SEO-optimised upload package for YouTube — metadata, thumbnail, and scheduled delivery to the publishing queue.

### G1 — Metadata Compilation

**Action:**
- Generate the following metadata assets using the master script, selected topic, and channel style card:

**Title:** Select the best-performing of the 3 title variants from `a3_selected_topic.json` based on: keyword presence, character count (40–60 chars optimal), and emotional hook strength.

**Description:**
```
[Hook sentence — first 125 chars are visible before "Show more"]
[2–3 sentence video summary]
[Chapter markers — paste from f1_chapter_markers.txt]
[Channel links and social handles]
[Relevant hashtags — max 3, channel-specific]
[Sponsor/affiliate disclosures if applicable]
```

**Tags:** Generate 15–20 tags: 3 broad niche tags, 5 mid-tail topic tags, 5 long-tail specific tags, 3 channel brand tags, and 2–4 trending tags from `a1_raw_topics.json`.

**Category:** Map channel niche to YouTube category ID from style card.

**Output:** `g1_metadata.json`

---

### G2 — Thumbnail Finalisation

**Action:**
- Load the winning thumbnail concept from `a3_selected_topic.json`.
- Generate the thumbnail base image via ComfyUI using thumbnail-specific parameters from style card:
  - Resolution: 1280×720
  - Style: high contrast, bold colours, single focal subject
  - Text overlay: channel-specific font, max 4 words, placed in designated text zone from style card
- Apply channel watermark from `/assets/brand/<channel_id>/watermark.png` at designated position.
- Run thumbnail QC:
  - No faces with closed eyes or distorted expressions
  - Text is fully visible and not clipped
  - Watermark is visible but not obscuring main subject
  - Passes YouTube thumbnail policy check (no misleading imagery flags)

**Output:** `/output/<job_id>/publish/thumbnail.jpg` (JPG, max 2MB)

---

### G3 — Scheduler & Queue Delivery

**Action:**
- Package the following for delivery to the publishing queue (`/api/publish/upload`):

```json
{
  "video_path": "/output/<job_id>/final/video_final.mp4",
  "thumbnail_path": "/output/<job_id>/publish/thumbnail.jpg",
  "metadata": "<g1_metadata.json contents>",
  "channel_id": "<youtube_channel_id from style card>",
  "scheduled_publish_time": "<ISO 8601 — from channel publishing calendar>",
  "privacy_status": "private",
  "notify_subscribers": true
}
```

- Privacy status is always `private` at upload. Scheduler changes to `public` at the specified publish time.
- Confirm queue acceptance and store the returned `upload_job_id` in the job manifest.

**Output:** `g3_upload_confirmation.json`

**Gate — G pass condition:** Upload job accepted by queue with a valid `upload_job_id`. Any rejection halts and returns the rejection reason.

---

## Step H — Short-Form Clips Pipeline

**Objective:** Extract 2–3 high-impact short-form clips from the long-form video, reformat for vertical platforms, and deliver to the short-form publishing queue for YouTube Shorts, TikTok, and Instagram Reels.

> **Agent Rule:** Step H runs in parallel with Step G — do not wait for G to complete before starting H. Both steps receive their inputs from Step F outputs.

---

### H1 — Peak Moment Identification

**Action:**
- Load `b1_master_script.json` and `b3_voiceover_pack.json`.
- Score every script section for short-form clip potential using these criteria:

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Standalone clarity | 35% | Can this section be understood without watching the full video? |
| Hook density | 30% | Does it contain a surprising fact, counter-intuitive claim, or strong statement? |
| Pacing | 20% | Is the narration pace fast enough to retain short-form viewers (≥ 130 wpm)? |
| Emotional peak | 15% | Does it trigger curiosity, surprise, or urgency? |

- Select the top 3 scoring sections as clip candidates.
- Each clip must be between 45 and 90 seconds when extracted.
- If a candidate section is shorter than 45 seconds, merge with an adjacent section if contextually coherent. If not coherent, skip and use the next candidate.

**Output:** `h1_clip_candidates.json` — list of 3 clips with: `section_ids`, `start_timestamp`, `end_timestamp`, `clip_score`, `clip_title`.

---

### H2 — Clip Extraction

**Action:**
- For each clip in `h1_clip_candidates.json`:
  - Extract the corresponding segment from `/output/<job_id>/final/video_final.mp4` using FFmpeg with frame-accurate cutting.
  - Preserve the mixed audio (voice + music) from the master mix.

**Output:** `/output/<job_id>/shorts/clips/` — named `clip_01_raw.mp4`, `clip_02_raw.mp4`, `clip_03_raw.mp4`.

---

### H3 — Vertical Reframe (16:9 → 9:16)

**Action:**
- Reframe each extracted clip from 16:9 (3840×2160) to 9:16 (1080×1920) for vertical platforms.
- Reframe strategy: intelligent centre-crop with subject-tracking. The crop window follows the primary visual subject throughout the clip duration.
- If the clip contains text overlays or on-screen graphics in the left/right margins that would be cropped out, use a split-screen layout instead:
  - Top 70%: cropped video
  - Bottom 30%: blurred wide-shot background with text overlay

**Output:** `/output/<job_id>/shorts/reframed/` — named `clip_01_vertical.mp4` etc. at 1080×1920, 60fps.

---

### H4 — Short-Form Subtitle Overlay

**Action:**
- Generate subtitles for each vertical clip using the existing `subtitles.srt` file (trim to clip timestamps).
- Apply short-form subtitle style — different from long-form:
  - Font size: larger (short-form viewers watch on mobile)
  - Position: centre-screen vertically (not lower third)
  - Style: bold, word-by-word highlight (karaoke style — current spoken word in accent colour, rest in white)
  - Max characters per line: 28 (narrower screen)
- Burn subtitles into each vertical clip.

**Output:** `/output/<job_id>/shorts/subtitled/` — named `clip_01_subtitled.mp4` etc.

---

### H5 — Short-Form Metadata Generation

**Action:**
- For each clip, generate platform-specific metadata:

**YouTube Shorts:**
```
Title: <clip_title from h1> #Shorts
Description: <1–2 sentences> + link to full video + channel hashtag
Tags: <5 tags from g1 metadata> + #Shorts + #<ChannelHashtag>
```

**TikTok:**
```
Caption: <hook sentence — max 150 chars> + 3–5 relevant hashtags
Sound: use original audio (do not replace with trending sound — preserves voice brand)
```

**Instagram Reels:**
```
Caption: <hook sentence> + call to action ("Full video on YouTube — link in bio") + 5–8 hashtags
Cover frame: select highest-contrast frame from clip as cover (do not use auto-generated cover)
```

**Output:** `h5_shorts_metadata.json`

---

### H6 — Short-Form Platform Delivery

**Action:**
- Package each clip with its platform metadata and deliver to the short-form publishing queue:
  - YouTube Shorts: schedule 24 hours after long-form publish time
  - TikTok: schedule 26 hours after long-form publish time
  - Instagram Reels: schedule 28 hours after long-form publish time
- Stagger the platform publish times to avoid simultaneous posting (which can dilute each platform's algorithm signal).

**Output:** `h6_shorts_upload_confirmations.json`

**Gate — H pass condition:** All 3 clips successfully accepted by publishing queue for all configured platforms.

---

## Job Completion & Manifest

On successful completion of all steps (G and H), the agent must generate a final job manifest:

```json
{
  "job_id": "<job_id>",
  "channel_id": "<channel_id>",
  "channel_name": "<channel_name>",
  "completed_at": "<ISO 8601 timestamp>",
  "topic": "<winning_topic>",
  "final_video": "/output/<job_id>/final/video_final.mp4",
  "long_form_upload_id": "<from g3>",
  "short_form_clips": [
    { "clip": "clip_01", "youtube_shorts_id": "...", "tiktok_id": "...", "reels_id": "..." },
    { "clip": "clip_02", "youtube_shorts_id": "...", "tiktok_id": "...", "reels_id": "..." },
    { "clip": "clip_03", "youtube_shorts_id": "...", "tiktok_id": "...", "reels_id": "..." }
  ],
  "gate_results": {
    "A": "pass", "B": "pass", "C": "pass", "D": "pass",
    "E": "pass", "F": "pass", "G": "pass", "H": "pass"
  },
  "human_checkpoint": {
    "approved_by": "<reviewer_id>",
    "approved_at": "<ISO 8601 timestamp>"
  }
}
```

Store manifest at `/output/<job_id>/job_manifest.json`.

---

## Error Handling — Global Rules

| Situation | Agent Action |
|-----------|-------------|
| Any gate fails | Halt immediately, return structured error with step ID, check name, and failure detail |
| API call fails | Retry once after 30 seconds. If second attempt fails, halt and log |
| File not found | Halt immediately — never proceed with a missing input file |
| Style card missing or incomplete | Halt at D0 — never generate visuals without a complete style card |
| Human checkpoint timeout (48h) | Escalate to channel manager — do not auto-approve |
| Node B (Topaz) unreachable | Retry after 5 minutes. If still unreachable after 3 attempts, proceed with pre-upscale resolution and flag in manifest |
| Output directory not writable | Halt immediately and alert |

---

## Troubleshooting FFmpeg Subtitle Burn-in (libass)

During final assembly (Step F4) or short-form subtitle overlay (Step H4), subtitle burn-in commands can fail if the system's FFmpeg binary was compiled without `libass` support. 

### Diagnostics:
To check if your active FFmpeg compilation has subtitle capabilities, run:
```bash
ffmpeg -buildconf | grep libass
```
Or search for the subtitle filter support directly:
```bash
ffmpeg -filters | grep subtitles
```

### Remediation:
1. **Fallback Copy Mode:** If the `subtitles` filter is unavailable, the pipeline scripts automatically catch the error, log a warning, and fall back to copying the unsuffixed video master directly to avoid pipeline blockage.
2. **Library Installation:** If subtitles are missing from the final video, install the required libraries and rebuild or re-install FFmpeg:
   ```bash
   # Debian/Ubuntu systems
   sudo apt-get install libass-dev
   # Re-install or acquire a static build with libass enabled
   ```

---

## Appendix — Required File Structure

```
/channels/
  <channel_id>/
    style_card.json          ← visual, audio, and tone parameters
    voice_profile.json       ← TTS voice settings + reference fingerprint
    publishing_calendar.json ← scheduled publish times

/assets/
  brand/
    <channel_id>/
      intro.mp4              ← channel intro bumper (≤5 sec, 3840×2160)
      outro.mp4              ← channel outro bumper (≤3 sec, 3840×2160)
      endscreen.mp4          ← end screen template (20 sec, 3840×2160)
      watermark.png          ← transparent PNG watermark
  music/
    <channel_id>/            ← local background music library

/output/
  <channel_id>/
    <job_id>/                ← all job outputs written here
```
