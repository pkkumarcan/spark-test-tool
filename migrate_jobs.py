#!/usr/bin/env python3
"""Migrate existing job directories into the job_store database."""

import os
import sys
import json
import time
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("OUTPUT_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "output"))

from app.backends.job_store import job_store

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

CHANNEL_MAP = {
    "MLN": 1, "RMR": 2, "NHZ": 3, "PKP": 4, "STM": 5, "ODA": 6,
    "DFW": 7, "ISL": 8, "BWA": 9, "DKS": 10, "CCL": 11, "GDB": 12
}

async def migrate():
    await job_store._ensure_init()
    
    existing_ids = set()
    rows = await job_store._db.execute_fetchall("SELECT job_id FROM jobs")
    for row in rows:
        existing_ids.add(row[0])
    
    count = 0
    for dirname in sorted(os.listdir(OUTPUT_DIR)):
        dirpath = os.path.join(OUTPUT_DIR, dirname)
        if not os.path.isdir(dirpath):
            continue
        if dirname in existing_ids:
            continue
        
        channel_id = None
        topic = ""
        content_type = "flagship"
        
        for code, num in CHANNEL_MAP.items():
            if code in dirname:
                channel_id = num
                break
        
        meta_path = os.path.join(dirpath, "metadata")
        if os.path.isdir(meta_path):
            for mf in os.listdir(meta_path):
                if mf == "channel.json":
                    try:
                        with open(os.path.join(meta_path, mf)) as f:
                            ch_data = json.load(f)
                        cid = ch_data.get("channel_id", "")
                        if cid in CHANNEL_MAP:
                            channel_id = CHANNEL_MAP[cid]
                    except Exception:
                        pass
                elif mf == "topic.json":
                    try:
                        with open(os.path.join(meta_path, mf)) as f:
                            t_data = json.load(f)
                        topic = t_data.get("title", t_data.get("topic_summary", ""))
                    except Exception:
                        pass
        
        if channel_id is None:
            channel_id = 1
        
        from datetime import datetime
        iso = datetime.utcnow().isocalendar()
        year_week = f"{str(iso[0])[-2:]}w{iso[1]:02d}"
        
        has_video = os.path.exists(os.path.join(dirpath, "final", "video_final.mp4"))
        has_audio = any(f.endswith(('.wav', '.mp3')) for f in os.listdir(os.path.join(dirpath, "audio")) if os.path.isdir(os.path.join(dirpath, "audio")))
        
        if has_video:
            status = "completed"
        elif has_audio:
            status = "completed"
        else:
            status = "completed"
        
        job_id = dirname
        now = time.time()
        
        try:
            await job_store._db.execute(
                """INSERT OR IGNORE INTO jobs (job_id, job_type, status, progress_pct, progress_msg,
                   result, error, created_at, updated_at, job_code, content_type, channel_id, year_week, parent_job_code)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (job_id, "pipeline", status, 100, "Migrated from disk",
                 json.dumps({"topic": topic}), None, now, now,
                 dirname, content_type, str(channel_id), year_week, None),
            )
            count += 1
        except Exception as e:
            print(f"  Skip {dirname}: {e}")
    
    await job_store._db.commit()
    print(f"Migrated {count} jobs into job_store")
    
    rows = await job_store._db.execute_fetchall("SELECT job_id, status, channel_id FROM jobs ORDER BY created_at DESC LIMIT 10")
    for row in rows:
        print(f"  {row[0]}: status={row[1]}, channel={row[2]}")

if __name__ == "__main__":
    asyncio.run(migrate())
