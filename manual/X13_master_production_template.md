# MEDIA FACTORY — MASTER PRODUCTION TEMPLATE
# Version 1.0 · All Channels · All Episodes

---

> ## HOW TO USE THIS FILE
>
> This is the master template for all 12 channels in the media factory network.
> Every new episode starts by duplicating this file and filling in the
> EPISODE-SPECIFIC sections. Do not change FIXED sections unless updating
> the channel's core configuration.
>
> **FIXED** = same every episode for this channel. Set once, do not touch.
> **EPISODE** = replaced for every new episode. Must be filled before generation.
>
> Duplicate this file, rename it:
> `[CHANNEL_CODE]_EP[NUMBER]_ProductionPack.md`
> Example: `ABV_EP002_ProductionPack.md`

---

---

# SECTION A — CHANNEL CONFIGURATION
# FIXED · Set once per channel · Do not change per episode

---

## A1. CHANNEL IDENTITY · FIXED

| Field | Value |
|---|---|
| Channel name | [CHANNEL NAME] |
| Channel handle | [@HANDLE] |
| Channel code | [e.g. ABV / BBP / HKP] |
| Original concept name | [e.g. Fiscal Flux] |
| Infrastructure email | [handle.yt@gmail.com] |
| Target niche | [Primary niche · Secondary niche · Tertiary niche] |
| Channel mantra | "[Mantra]" |
| CPM tier | $[low]–[high] · [Niche label] |
| Launch phase | Phase [1 / 2 / 3] |
| Pipeline type | [Standard narration / Music-first / Fast-cut narration] |

---

## A2. AVATAR IDENTITY · FIXED

| Field | Value |
|---|---|
| Avatar name | [Name] (The [Title]) |
| Voice register | [e.g. Measured, authoritative, dry wit. Never alarmist.] |
| Tone | [e.g. Institutional insider — briefing a private client] |
| Target viewer | [Age range, profession, intent] |
| Avoid | [List what breaks the persona] |

### Avatar visual spec · FIXED
```
[Full visual persona description — style, clothing, backdrop, lighting]
[Copy directly from channel directory document]
```

### ComfyUI prompt — full frame · FIXED
```
[Paste final approved ComfyUI generation prompt]
[This should not change between episodes]
```

### ComfyUI prompt — watermark variant · FIXED
```
[Same as above, desaturated 80%, opacity 30%,
small format, bottom-right corner placement,
no background, transparent PNG output]
```

### Avatar motion loop spec · FIXED
```
Subtle: slight breathing motion, 2s loop,
no head movement, no lip sync required,
tool: Pika or Kling — "subtle breathing, stationary portrait, loop"
```

---

## A3. VISUAL STYLE · FIXED

| Element | Value |
|---|---|
| Background | [Hex code] |
| Primary text | [Hex code] |
| Accent colour | [Hex code] |
| Alert / highlight | [Hex code] |
| Avatar style | [e.g. Coloured pencil sketch on textured paper] |
| Avatar on data slides | Watermark at 30% opacity · bottom-right |
| Avatar on hook / CTA | Full frame |
| Stock footage | None — all visuals generated programmatically |
| Font | Sans-serif · bold for headlines · regular for data labels |

---

## A4. TTS / VOICE CLONE SETTINGS · FIXED

| Parameter | Value |
|---|---|
| Tool | [ElevenLabs / Kokoro local] |
| Voice ID | `[avatar_voice_id]` |
| Stability | [0.00–1.00] |
| Similarity boost | [0.00–1.00] |
| Style | [0.00–1.00] |
| Speaker boost | [true / false] |
| Model | `[model_id]` |
| Output format | MP3 · 44.1kHz · 320kbps |

---

## A5. MUSIC BED SPEC · FIXED

| Parameter | Value |
|---|---|
| Genre | [e.g. Corporate ambient / sparse piano / minimal percussion] |
| BPM | [~100] |
| Suno generation prompt | `[full suno prompt for this channel's music style]` |
| Level under VO | –18dB |
| Hook level | –14dB |
| From point 1 onward | –20dB |
| CTA | Fade to silence — VO carries alone |

---

## A6. OUTPUT SPECS · FIXED

| Format | Spec |
|---|---|
| Main video | 1920×1080 · 30fps · H.264 · AAC 320kbps |
| Shorts cutdown | 1080×1920 · Hook only (0–20s) · reframed |
| Max file size | 2GB |
| Colour space | sRGB |
| Render tool | FFmpeg pipeline via n8n |

---

## A7. PERFORMANCE TARGETS · FIXED

| Metric | Target | Flag if below |
|---|---|---|
| CTR | > 6% at 48h | < 4% → swap to Variant B thumbnail |
| AVD | > 55% of runtime | < 40% → audit hook, shorten to 8 words max |
| RPM | > $[channel minimum] | < $[floor] → review tags and category |
| Views 72h | 1,000+ | < 500 → boost as Shorts cutdown |

### Feedback loop logic · FIXED
```
IF CTR < 4% at 48h       → swap thumbnail to Variant B
IF AVD < 40%             → hook too long — shorten next script to 8 words max
IF RPM < floor           → check tags, recategorise, review title keywords
IF views > 1k in 72h     → flag as WINNER — clone topic angle for next episode
IF winner confirmed       → log: topic + hook structure + thumbnail style
                            into channel prompt library for next generation cycle
```

---

---

# SECTION B — EPISODE PRODUCTION PACK
# EPISODE · Fill fresh for every new episode

---

## B1. EPISODE OVERVIEW · EPISODE

| Field | Value |
|---|---|
| Channel | [Channel name · @handle] |
| Episode ID | [CHANNEL_CODE-EP000] |
| Avatar | [Name (The Title)] |
| Status | [ ] Topic selected · [ ] Script written · [ ] Ready for generation |
| Topic | [One sentence — what this episode is about] |
| Angle | [The counter-intuitive take or tension that makes this watchable] |
| Target duration | 95–100 seconds |
| Word count | ~195 words |
| Format | YouTube landscape 1920×1080 + Shorts cutdown 1080×1920 |
| Publish window | [Day range · Time EST] |

---

## B2. SCRIPT · EPISODE

> Delivery mark key:
> `|` = short pause (0.8s) · `||` = long pause (1.5s)
> `**word**` = emphasis — slightly slower, lower pitch
> `~~phrase~~` = slow down here
>
> Rule: Hook must create tension or state a counter-intuitive fact.
> Never open with "Welcome to [channel name]."

---

### HOOK · 0–8 sec · EPISODE

[Write the hook here — 1 to 3 short sentences maximum.
Opens mid-thought or with a tension. No introduction.]

> Direction: [Specific delivery note for this hook]

---

### POINT 1 — [Label the situation in 3 words] · 8–38 sec · EPISODE

[Write point 1 here — establishes the situation or the problem.
Short sentences. One idea per line. End on a tension.]

> Direction: [Specific delivery note for point 1]

---

### POINT 2 — [Label the mechanism in 3 words] · 38–68 sec · EPISODE

[Write point 2 here — explains the mechanism, the "why behind the why".
This is where the insider insight lives. End on a consequence.]

> Direction: [Specific delivery note for point 2]

---

### POINT 3 — [Label the insight in 3 words] · 68–88 sec · EPISODE

[Write point 3 here — the actionable payoff.
Name specific things the viewer can do or look for.
End on a statement that makes the gap feel urgent.]

> Direction: [Specific delivery note for point 3]

---

### CTA · 88–100 sec · EPISODE

[Write CTA here — one clear action only.
Name the channel. Tease the next video specifically.
Never generic — "subscribe for more" is not enough.]

> Direction: Measured pace. Music fades here — VO carries alone to the end.

---

### PLAIN TEXT VERSION · EPISODE
> Strip all marks. Paste directly into TTS tool. No formatting.

```
[Full script as clean plain text — no pipes, no asterisks,
no tildes, no direction notes. One paragraph per section.
Proofread for broken punctuation before pasting.]
```

---

## B3. AUDIO MIX SEQUENCE · EPISODE

> Timestamps change per episode based on script pacing.
> Use section A5 for all dB levels — do not repeat them here.

```
00:00  Music in at –14dB
00:00  [Avatar name] VO begins (hook)
00:0X  Music fades to –20dB · VO continues (point 1)
01:XX  Music begins fade out over 4 seconds
01:XX  VO (CTA) — music fully out
01:XX  VO ends · 1s silence · end card audio sting
```

---

## B4. FRAME SEQUENCE · EPISODE

> Visual style, hex codes, avatar spec — all in section A3.
> Only describe what appears on screen per frame. Do not repeat style rules.

```
FRAME 1 · HOOK · 0–8 sec
  - [Avatar name] avatar: chest-up, front view, minimal motion loop
  - On-screen text overlay: "[Short punchy line from hook — 4 words max]"
  - Background: [channel background colour]
  - No B-roll

FRAME 2 · POINT 1 · 8–38 sec
  - [Describe the data visual — chart type, what it shows, animation direction]
  - [Describe what is highlighted and in which accent colour]
  - [Avatar name] avatar watermark bottom-right at 30% opacity

FRAME 3 · POINT 2 · 38–68 sec
  - [Describe the data visual — diagram type, what it illustrates]
  - [Describe how elements appear in sync with VO]
  - [Avatar name] avatar watermark bottom-right at 30% opacity

FRAME 4 · POINT 3 · 68–88 sec
  - [Describe the comparison or insight visual]
  - [Describe labels, brackets, or callouts]
  - [Avatar name] avatar watermark bottom-right at 30% opacity

FRAME 5 · CTA · 88–100 sec
  - [Avatar name] avatar: full frame, front view
  - Subscribe card overlay: channel name + bell icon
  - End card begins at 95s: next video preview placeholder
  - Background: [channel background colour]
```

---

## B5. THUMBNAIL SPEC · EPISODE

> Channel visual style in section A3. Only describe layout and text here.

### Variant A — upload first
```
Layout:     [Describe composition — avatar position, text position]
Avatar:     [Describe pose and framing]
Headline:   "[HEADLINE IN CAPS]" — white, bold, 80pt
Subline:    "[Supporting line]" — [accent colour] block behind, 48pt
Background: [Channel background hex]
Border:     None
```

### Variant B — swap if Variant A CTR < 4% at 48h
```
Layout:     [Describe alternative composition]
Centre:     [Describe data visual or graphic used]
Top text:   "[Alternative headline]" — white bold
Avatar:     [Small, positioned corner, attitude toward the graphic]
Background: [Channel background hex]
```

### Generation prompt — Variant A
```
[Full image generation prompt — background, avatar description,
text content, style, dimensions 1280×720]
```

### Generation prompt — Variant B
```
[Full image generation prompt — background, graphic description,
text content, style, dimensions 1280×720]
```

---

## B6. UPLOAD METADATA · EPISODE

### Title
```
[YouTube SEO title — counter-intuitive, specific, under 60 characters]
```

### Description
```
[Hook sentence — what the viewer will learn. Must work above the fold
within the first 150 characters.]

In this video:
00:00 — [Chapter 1 label]
00:38 — [Chapter 2 label]
01:08 — [Chapter 3 label]

[One sentence channel value proposition.]
[Channel subscribe line.]

#[Tag1] #[Tag2] #[Tag3] #[Tag4] #[Tag5]
```

### Tags
```
[10–15 comma-separated tags — mix of broad niche terms and specific
episode keywords. No tags unrelated to the episode topic.]
```

### Upload settings

| Field | Value |
|---|---|
| Category | [YouTube category name · ID number] |
| Language | English |
| Made for kids | No |
| Visibility | Scheduled |
| Publish time | [Day · Time EST] |
| End screen | Yes — at 95s |
| Cards | Yes — at 45s · link to next video |
| Thumbnail | Variant A on upload |

---

---

# SECTION C — GENERATION CHECKLIST
# EPISODE · Tick each item as completed · Nothing pre-ticked

---

```
EPISODE ID: [CHANNEL_CODE-EP000]
CHANNEL:    [Channel name]
DATE:       [Date started]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AUDIO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Generate music bed via Suno
      Prompt: section A5
      Output: [CHCODE]_EP[000]_music_bed.mp3

[ ] Generate VO via TTS tool
      Input: plain text block in section B2
      Settings: section A4
      Output: [CHCODE]_EP[000]_vo_raw.mp3

[ ] Review VO — check for mispronunciations, broken pacing
[ ] Mix VO + music bed per sequence in section B3
      Output: [CHCODE]_EP[000]_audio_mix.mp3

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVATAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Generate avatar full frame via ComfyUI
      Prompt: section A2
      Output: [CHCODE]_EP[000]_avatar_fullframe.png

[ ] Generate avatar watermark PNG via ComfyUI
      Prompt: section A2 watermark variant
      Output: [CHCODE]_EP[000]_avatar_watermark.png

[ ] Generate avatar motion loop via Pika / Kling
      Spec: section A2 motion loop
      Output: [CHCODE]_EP[000]_avatar_loop.mp4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VIDEO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Generate Frame 2 visual — [brief label from B4]
[ ] Generate Frame 3 visual — [brief label from B4]
[ ] Generate Frame 4 visual — [brief label from B4]

[ ] Stitch all frames + audio via FFmpeg
      Frame sequence: section B4
      Audio: [CHCODE]_EP[000]_audio_mix.mp3
      Output: [CHCODE]_EP[000]_main_1920x1080.mp4

[ ] Export Shorts cutdown — hook only (0–20s) reframed
      Output: [CHCODE]_EP[000]_shorts_1080x1920.mp4

[ ] QC review — watch full video, check sync, check text overlays

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
THUMBNAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Generate Variant A
      Prompt: section B5
      Output: [CHCODE]_EP[000]_thumb_A.jpg

[ ] Generate Variant B
      Prompt: section B5
      Output: [CHCODE]_EP[000]_thumb_B.jpg

[ ] QC review — check text legibility at small size (mobile preview)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UPLOAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Upload main video to YouTube
[ ] Paste title from section B6
[ ] Paste description from section B6
[ ] Paste tags from section B6
[ ] Apply upload settings from section B6
[ ] Set Variant A as thumbnail
[ ] Set end screen at 95s
[ ] Set card at 45s — link to next video
[ ] Schedule publish time

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRACKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ] Log publish date and time
[ ] Check CTR + AVD at 48h — apply feedback loop (section A7)
[ ] Check RPM at 72h
[ ] Log results to channel performance tracker
[ ] If WINNER — add to channel prompt library
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

---

# SECTION D — REFERENCE: ALL 12 CHANNELS
# FIXED · Network-wide reference · Do not edit per episode

---

## Phase 1 — Launch first · Highest CPM

| Code | Channel | Handle | Avatar | Niche | CPM |
|---|---|---|---|---|---|
| ABV | A Banker's View | @ABankersView | Sterling (The Analyst) | Finance · Macro · Crypto · Wealth | $12–22 |
| BBP | A Builder's Blueprint | @BuildersBlueprint | Turing (The Architect) | Applied AI · Automation · n8n · Local LLM | $10–18 |
| HKP | A Hacker's Protocol | @HackersProtocol | Knox (The Guardian) | Cybersecurity · Privacy · Crypto protection | $10–16 |

## Phase 2 — Add after Phase 1 is stable

| Code | Channel | Handle | Avatar | Niche | CPM |
|---|---|---|---|---|---|
| FVS | A Futurist's Vision | @FuturistsVision | Kepler (The Futurist) | Space · Future tech · AI · Sci-fi | $6–12 |
| JRV | A Juror's Verdict | @JurorsVerdict | Vance (The Investigator) | Legal commentary · Forensic analysis | $8–15 |
| RPB | A Reporter's Brief | @ReportersBrief | Reed (The Anchor) | Geopolitics · Tech policy · Supply chain | $7–13 |
| BHC | A Biohacker's Code | @BiohackersCode | Nova (The Coach) | Biohacking · Sleep · Nutrition · Cognition | $8–14 |
| STP | A Stoic's Path | @StoicsPath | Sage (The Mentor) | Stoicism · Resilience · Philosophy | $5–9 |
| NMC | A Nomad's Compass | @NomadsCompass | Miles (The Explorer) | Travel · Digital nomad · Geo-arbitrage | $4–8 |

## Phase 3 — Separate pipeline variants

| Code | Channel | Handle | Avatar | Niche | CPM | Pipeline note |
|---|---|---|---|---|---|---|
| CRC | A Curator's Corner | @CuratorsCorner | Pixel (The Geek) | Viral trivia · Riddles · History | $3–7 | Fast-cut narration |
| SKV | A Seeker's Verse | @SeekersVerse | Kabir (The Scholar) | SGGS · Vedas · Bhagavad Gita | $4–8 | Meditative narration |
| LSA | A Listener's Aura | @ListenersAura | Melody (The DJ) | Lofi · Ambient · Focus · Sleep | $1–3 | Music-first · No script |

---

## Script rules that apply to all channels · FIXED

```
HOOK RULES
- Never open with "Welcome to [channel name]"
- Never announce what you are about to say — say it
- Hook must create tension OR state a counter-intuitive fact
- Hook must work as a standalone sentence if clipped for Shorts
- Maximum 3 sentences · Maximum 8 seconds

BODY RULES
- Point 1: establish the situation — what is happening
- Point 2: explain the mechanism — why it is happening
- Point 3: deliver the actionable insight — what to do with it
- Each point: 3–6 sentences · 20–30 seconds
- One idea per sentence · Short sentences preferred
- No filler transitions: "Now let's talk about..." "Moving on..."
- No year references that will age the script — use "recently" or "this cycle"

CTA RULES
- One action only — subscribe
- Name the channel explicitly
- Tease the next video with a specific topic — not "more great content"
- Maximum 15 seconds
- Music out before CTA — VO carries alone

PERSONA RULES
- Every script must be written with the channel's avatar persona injected
- Never generate a script without the persona lock from section A2 active
- If a script sounds like it could belong to any channel — rewrite it
- Cross-channel contamination (wrong topic for the channel) = immediate reject
```

---

*Master Production Template v1.0 · Media Factory Network · 12 channels*
*Fixed sections reviewed: 2026-06-17 · Next review: 2026-09-17*
