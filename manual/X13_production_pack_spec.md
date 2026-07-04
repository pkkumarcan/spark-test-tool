# X13 — Full Production Pack Specification

## Chapter Card
**Chapter:** `X13 — Full Production Pack Specification`  
**Layer:** `Planning`  
**Status:** `implemented`  
**Purpose (1 line):** `Define the standardized schema for generating YouTube Episode Production Packs`  
**Last Verified:** `2026-06-17`

---

## 1) Overview of the Schema
The **Full Production Pack** is a comprehensive, 10-section document designed to define all metadata, script content, TTS inputs, image generation parameters, mixing guidelines, and tracking parameters for a single video episode. 

This schema acts as the **Single Source of Truth (SSoT)** for downstream automation agents (e.g., n8n, Python asset generators, and video assembly pipelines).

---

## 2) Config & Standards (The 10-Section Schema)

Each episode production pack must contain exactly the following 10 sections:

1. **Episode Overview**: At-a-glance table specifying topics, target duration, word count, video format, publication scheduling, and the niche's CPM tier.
2. **Channel Persona Lock**: Defines voice registers, tone guidelines, the target audience, explicit things to avoid (e.g., clickbait, crypto maximalism), and the channel mantra.
3. **Audio Script (Full Read)**: 
   - **Delivery Markers**: Script annotated with delivery cues:
     - `|` = short pause (0.8s)
     - `||` = long pause (1.5s)
     - `**word**` = pitch/emphasis change
     - `~~phrase~~` = slow down pace
   - **Plain Text TTS Block**: A clean, copy-pasteable version wrapped in a markdown code block for direct ingestion by ElevenLabs or local Kokoro models.
4. **Audio Production Spec**: Configures ElevenLabs/Kokoro parameters (stability, similarity, style), Suno/Audiocraft music prompts, volume levels (in dB), and timeline sequence mixing logs.
5. **Video Production Spec**: Defines hex color palettes, font styles, and a frame-by-frame storyboard mapping timestamps to visual representations.
6. **Avatar Generation Spec**: Holds Stable Diffusion / ComfyUI text prompts for full-frame character rendering, desaturated watermarks, and subtle motion loops.
7. **Thumbnail Spec**: Visual specifications for Variant A and Variant B, plus the exact ComfyUI or Canva text prompts for generation.
8. **Upload Metadata**: Title, Description (with chapter timestamps), Tags, and programmatic Upload Settings.
9. **Performance Tracking**: Target metrics (CTR, AVD, RPM) and conditional feedback loop actions (e.g., swapping thumbnails if CTR is underperforming).
10. **Generation Checklist**: An actionable task list for verification.

---

## 3) Why this Schema is Optimal for LLMs & Automation

1. **Structured Parsability**: The division into numbered markdown sections with clear tables and code blocks allows automation scripts (Regex, JSON loaders) to cleanly extract settings without parsing human conversational noise.
2. **Constraint Enforcement**: Including word count targets, durations, and strict "avoid" rules keeps the generation within boundaries and prevents AI hallucinations.
3. **Decoupled Architecture**: Downstream nodes can execute tasks in parallel (e.g., generating audio in ElevenLabs while simultaneously rendering avatars in ComfyUI) using configurations defined in the same pack.
