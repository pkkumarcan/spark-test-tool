#!/bin/bash
# Create template files for all planned chapters

TEMPLATE_DIR="/home/pkkumar/AGGY/spark-test-tool/manual"

# Foundation (X02, X07, X08)
chapters=(
  "X02|Factory Contract|Foundation|planned|Define job manifest, folder schema, naming conventions, and DoD|2h"
  "X07|Operations Runbook|Foundation|planned|Daily/weekly maintenance checklists and housekeeping|1d"
  "X08|Smoke Tests & Benchmarking|Foundation|planned|Standard benchmark suite with quality/speed scoring|1d"
  
  # Planning (X13-X20)
  "X13|Master Story Script|Planning|planned|Generate narrative script with structure and pacing|30m"
  "X14|Voiceover Script Pack|Planning|planned|Create performance-ready VO with pauses and pronunciation|30m"
  "X15|Visual Script Pack|Planning|planned|Generate shot list with prompts, durations, and seeds|30m"
  "X16|Music Script Pack|Planning|planned|Create music brief with mood, tempo, and structure|20m"
  "X17|Edit Blueprint (EDL-lite)|Planning|planned|Build timing map for assembly with scene cuts and beats|20m"
  "X18|Publishing Package Draft|Planning|planned|Generate titles, descriptions, tags, and CTAs|15m"
  "X19|Blueprint QA & Compliance|Planning|planned|QA pass for factuality, policy, and IP risks|20m"
  "X20|Production Blueprint Export|Planning|planned|Export single manifest tying all scripts together|10m"
  
  # Audio-Speech (X23-X26)
  "X23|Voice Cloning Profiles|Audio-Speech|planned|Create and manage reusable voice profiles|2h"
  "X24|Character Voices / Voice Conversion|Audio-Speech|planned|Multi-character pipeline with conversion rules|1h"
  "X25|Speech QC|Audio-Speech|planned|QC checks for noise, intelligibility, and pacing|15m"
  "X26|Speech Post-Processing|Audio-Speech|planned|Cleanup chain with EQ, compression, and denoising|30m"
  
  # Audio-Music (X31-X32, X34-X36)
  "X31|Music Asset Library|Audio-Music|planned|Organize packs, libraries, tagging, and licensing|2h"
  "X32|DAW Templates|Audio-Music|planned|Create reusable DAW templates with routing and stems|1h"
  "X34|Arrangement for Video|Audio-Music|planned|Align music to story beats with cueing and transitions|30m"
  "X35|Mixing Workflow|Audio-Music|planned|Mix stems with bus routing, FX, and automation|1h"
  "X36|Mastering Standards|Audio-Music|planned|Final loudness, true peak, and platform exports|30m"
  
  # Images (X43-X44, X46-X47)
  "X43|Style Consistency|Images|planned|Maintain character/scene consistency with ControlNet and LoRA|1h"
  "X44|Thumbnail Factory|Images|planned|Produce thumbnail variants for A/B testing|30m"
  "X46|Brand Assets|Images|planned|Generate logos, overlays, masks, and typography|1h"
  "X47|Image QC|Images|planned|Visual QC for artifacts, brand rules, and safety|20m"
  
  # Video (X54-X55, X57)
  "X54|Video→Video Workflows|Video|planned|Restyle, enhance, and maintain continuity|30m"
  "X55|Continuity System|Video|planned|Track characters, scenes, and prompt/seed discipline|30m"
  "X57|Topaz Rescue & Polish|Video|planned|Rescue layer for hard cases and final polish|30m"
  
  # Assembly (X61, X63-X67)
  "X61|Assembly Rules|Assembly|planned|Build timeline structure with pacing and scene stitching|1h"
  "X63|Subtitles Pipeline|Assembly|planned|Generate SRT with styling and burn-in options|30m"
  "X64|Thumbnail Finalization|Assembly|planned|Final exports, crops, safe margins, and variants|15m"
  "X65|ffmpeg Cookbook|Assembly|planned|Standard export recipes and presets|20m"
  "X66|Versioning & Review Exports|Assembly|planned|v1/v2/v3 approvals and review workflow|15m"
  "X67|Deliverables Bundle|Assembly|planned|Produce masters, shorts, cutdowns, and archive|30m"
  
  # Publishing (X71-X75)
  "X71|Channel Setup|Publishing|planned|Configure branding, defaults, and upload presets|20m"
  "X72|Upload Package Generator|Publishing|planned|Package metadata, assets, and filenames|15m"
  "X73|Scheduling & Calendar|Publishing|planned|Manage cadence and batch uploads|20m"
  "X74|Platform Export Presets|Publishing|planned|YT long/shorts, reels, tiktok presets|15m"
  "X75|Release Checklist|Publishing|planned|Final QC, legal, brand, and go/no-go|10m"
  
  # Post-Publishing (X81-X85)
  "X81|KPI Dashboard|Post|planned|Define and track CTR, retention, hook rate, AVD|2h"
  "X82|Weekly Review System|Post|planned|Weekly loop: wins, fails, next actions|30m"
  "X83|Experiment System|Post|planned|A/B testing framework for thumbnails, hooks, CTAs|1h"
  "X84|Feedback Loops|Post|planned|Push learnings into templates and workflows|30m"
  "X85|Community Ops|Post|planned|Comment strategy, moderation, repurposing|30m"
  
  # Governance (X91, X93-X100)
  "X91|Legal/IP/Compliance|Governance|planned|Licensing, attribution, risk scoring|1h"
  "X93|Monetization Overview|Governance|planned|Offers, positioning, and ethics|30m"
  "X94|Funnels & Products|Governance|planned|Lead magnets, landing pages, email sequences|1h"
  "X95|Tracking & Attribution|Governance|planned|Conversion events and reporting|30m"
  "X96|Costing & ROI|Governance|planned|Compute cost, time cost, upgrade triggers|30m"
  "X97|Upgrade Strategy|Governance|planned|GPU, models, tools, deprecation policy|20m"
  "X98|Incident Response|Governance|planned|Triage, rollback, fix, prevention|30m"
  "X99|Appendices|Governance|planned|Templates, checklists, schemas|1h"
  "X100|Master Change Log|Governance|planned|Track what changed and why|10m"
)

for entry in "${chapters[@]}"; do
  IFS='|' read -r id title layer status purpose time <<< "$entry"
  filename="${id}_$(echo $title | tr '[:upper:]' '[:lower:]' | tr ' &' '_' | tr -d "'")"
  
  cat > "$TEMPLATE_DIR/$filename.md" << CHAPER
---
chapter_id: $id
title: "$title"
layer: "$layer"
status: "$status"
purpose: "$purpose"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "$time"
inputs:
  - "<TBD>"
outputs:
  - "<TBD>"
qc_gates:
  - "<TBD>"
default_tools:
  primary: "<TBD>"
  fallback: "<TBD>"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_$id"
  run: "run_$id"
  score: "score_$id"
  retry: "retry_$id"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# $id — $title

## Chapter Card
**Chapter:** \`$id — $title\`  
**Layer:** \`$layer\`  
**Status:** ❌ PLANNED  
**Purpose (1 line):** $purpose  
**Last Verified:** 2026-06-15

**Status:** This chapter is planned but not yet implemented.

---

## 1) Quickstart (Golden Path)

### Goal
$purpose

### When to run
- TBD

### Golden Path Steps
1) TBD

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| TBD | — | — |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| TBD | — | — |

### Definition of Done (DoD)
TBD

---

## 3) Tooling (Approved Stack)

### Primary (default)
- **Tool:** TBD

---

## 4) Troubleshooting

### Issue 1 — TBD
- **Cause:** TBD
- **Fix:** TBD

---

## 5) Change Log

- 2026-06-15 — Template created (not yet implemented)
CHAPER

  echo "Created: $filename.md"
done
