---
chapter_id: X67
title: "Deliverables Bundle"
layer: "Assembly"
status: "implemented"
purpose: "Produce and zip final publish bundle (video, thumbnail, descriptions, and SRT files)"
owner: "Human/Agent"
last_updated: "2026-06-15"
estimated_time: "30m"
inputs:
  - "subtitled_final.mp4"
  - "thumbnail_1280x720.png"
  - "job_manifest.json"
outputs:
  - "bundle_archive.zip"
qc_gates:
  - "archive_not_corrupt == True"
  - "files_included_count == 4"
default_tools:
  primary: "Python/zipfile"
  fallback: "tar CLI"
smoke_tests:
  - "A_minimal"
  - "B_standard"
hooks:
  validate: "validate_X67"
  run: "run_X67"
  score: "score_X67"
  retry: "retry_X67"
status:
  state_machine: "NOT_STARTED -> RUNNING -> PASSED | FAILED -> RETRIED -> PASSED | ESCALATE"
  max_retries: 3
---

# X67 — Deliverables Bundle

## Chapter Card
**Chapter:** `X67 — Deliverables Bundle`  
**Layer:** `Assembly`  
**Status:** ✅ IMPLEMENTED  
**Purpose (1 line):** Gather all final output components (video, thumbnail, subtitles, metadata description) and pack them into a compressed archive.  
**Last Verified:** 2026-06-15  

**Inputs (files/keys):**
- `/jobs/<job_id>/subtitled_final.mp4` (finished video cut)
- `/jobs/<job_id>/publish/thumbnail_1280x720.png` (finished thumbnail)
- `/jobs/<job_id>/99_logs/X63/transcription.srt` (subtitle track)
- `job_manifest.json` (metadata descriptions)

**Outputs (files):**
- `/jobs/<job_id>/publish/bundle_<job_id>.zip`

**Quality Gates (must pass):**
- `archive_not_corrupt == True`: The generated ZIP file must open and test valid without block checksum errors.
- `files_included_count == 4`: Zip archive must contain exactly the master video, thumbnail, SRT file, and description txt.

**Default tools:**
- `Python/zipfile` (primary ZIP encoder library)
- `tar CLI` (fallback compression utility)

**Automation hooks:**
- `validate_X67(job_id)`
- `run_X67(job_id, profile)`
- `score_X67(job_id)`
- `retry_X67(job_id, strategy)`

**Smoke test time:** `~5 min`  
**Owner:** `Human/Agent`  
**Last updated:** `2026-06-15`  

---

## 1) Quickstart (Golden Path)

### Goal
Collect and bundle all publishing deliverables into a single package ready for social platform upload APIs.

### When to run this chapter
- Immediately after review approvals are confirmed (Chapter X66).
- Prior to triggering publishing uploads (Chapter X72).

### Default steps (golden path)
1) Resolve paths to the approved video, thumbnail, SRT file, and manifest metadata description.
2) Create the target output directory `/jobs/<job_id>/publish/`.
3) Instantiate a zip writer object in Python and write all four assets.
4) Save the file as `bundle_<job_id>.zip` and log the byte size to the manifest.

### Done looks like
- [ ] Output exists: `/jobs/<job_id>/publish/bundle_<job_id>.zip`
- [ ] QC passed: Zip extraction tests successfully.
- [ ] Manifest updated: `job_manifest.json -> pipeline_steps[X67]`

---

## 2) Factory Contract (Inputs → Outputs → DoD)

### Required Inputs
| Input | Path/Key | Notes |
|-------|----------|-------|
| Final Video | `/jobs/<job_id>/subtitled_final.mp4` | Synced subtitled master |
| Thumbnail PNG | `/jobs/<job_id>/publish/thumbnail_1280x720.png` | Finished thumbnail image |
| Subtitles SRT | `/jobs/<job_id>/99_logs/X63/transcription.srt` | Caption track |
| Metadata | `job_manifest.json` | JSON/text meta fields |

### Required Outputs
| Output | Path | Notes |
|--------|------|-------|
| Output Archive | `/jobs/<job_id>/publish/bundle_<job_id>.zip` | Export bundle |

### Definition of Done (DoD)
`Artifacts exist + QC passed + logs saved + manifest updated.`

---

## 3) Config & Standards (Single Source of Truth)

### Bundle Manifest Schema
The archive bundle must include the following naming format:
- `video.mp4` (remapped from subtitled_final.mp4)
- `thumbnail.png` (remapped from thumbnail_1280x720.png)
- `subtitles.srt` (remapped from transcription.srt)
- `description.txt` (extracted text from job_manifest.json)

---

## 4) Tooling (Approved Stack)

### Primary (default)
- **Tool/Model:** Python standard library `zipfile`
  - **Version/pin:** Python 3.11+
  - **Compute notes:** CPU execution (approx. 5-10 seconds depending on video size).

---

## 5) Procedure (Operator Steps)

### Step 1 — Create ZIP Deliverables Pack
- **Inputs:** Paths to files.
- **Action:**
  - Execute a python routine:
    ```python
    import zipfile
    import os
    
    def pack_bundle(zip_path, file_maps):
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for src, dest in file_maps.items():
                if os.path.exists(src):
                    zipf.write(src, dest)
    ```
- **Expected output:** A compressed ZIP file containing all mapped deliverables.
- **Common failures:** Input file missing.
- **Fix:** Pre-verify that each source path exists on the filesystem.

---

## 6) Smoke Tests (Mandatory)

### Smoke Test A — Minimal (fast)
- **Goal:** Zip a directory containing mock dummy text files.
- **Pass criteria:** ZIP file generated is valid and readable.

---

## 7) QC Checklist + Scoring

### QC checklist (tick-box)
- [ ] ZIP archive is valid and tests OK.
- [ ] File count is exactly 4.

---

## 9) Metrics to Record (for Optimization)

Record into logs/DB:
- `bundle_size_bytes`
- `compression_ratio`

---

## 10) Troubleshooting (Top Issues)

### Issue 1 — ZIP File size limit exceeded
- **Cause:** Video file is larger than 2GB (limits on some standard ZIP decoders).
- **Fix:** Use ZIP64 extensions: `zipfile.ZipFile(..., allowZip64=True)`.

---

## 11) Change Log (Chapter Local)

- 2026-06-15 — Wrote archive packaging guidelines.
