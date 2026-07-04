import os
import aiosqlite
import email.utils
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.mail_agent.mail_agent import (
    sync_status, start_sync_task, stop_sync, start_cleanup_task,
    start_stage_sender, start_stage_senders, start_keyword_purge,
    start_empty_trash, get_imap_folders_task, get_keyword_segment_counts
)
from app.mail_agent import db_setup

router = APIRouter()

class StartSyncRequest(BaseModel):
    folder: str = "INBOX"
    segment: str = "all"

@router.post("/sync/start")
async def start_sync_endpoint(req: StartSyncRequest = StartSyncRequest()):
    if sync_status.is_running:
        return {"status": "already_running"}
    await start_sync_task(req.folder, req.segment)
    return {"status": "started"}

@router.get("/folders")
async def get_folders_endpoint():
    try:
        folders = await get_imap_folders_task()
        return {"folders": folders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/stop")
async def stop_sync_endpoint():
    stop_sync()
    return {"status": "stopped"}

@router.get("/stats")
async def get_stats_endpoint():
    # Calculate database size
    db_size_bytes = 0
    if os.path.exists(db_setup.DB_PATH):
        db_size_bytes = os.path.getsize(db_setup.DB_PATH)
        
    return {
        "is_running": sync_status.is_running,
        "total_emails": sync_status.total_emails,
        "synced_emails": sync_status.synced_emails,
        "current_speed_ups": round(sync_status.current_speed, 1),
        "status": sync_status.status,
        "error_message": sync_status.error_message,
        "db_size_mb": round(db_size_bytes / (1024 * 1024), 2),
        "logs": sync_status.logs,
        "purge_queue": sync_status.purge_queue,
        "purging_senders": sync_status.purging_senders
    }

@router.get("/emails")
async def get_emails_endpoint(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: str = Query(None)
):
    offset = (page - 1) * limit
    db_path = db_setup.DB_PATH
    
    if not os.path.exists(db_path):
        return {"emails": [], "total_count": 0, "page": page, "limit": limit}

    emails = []
    total_count = 0

    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            db.row_factory = aiosqlite.Row
            
            # Construct query
            where_clause = ""
            params = []
            
            if search:
                where_clause = "WHERE sender LIKE ? OR subject LIKE ?"
                search_param = f"%{search}%"
                params = [search_param, search_param]
            
            # Fetch count
            count_query = f"SELECT COUNT(*) FROM emails {where_clause}"
            async with db.execute(count_query, params) as cursor:
                row = await cursor.fetchone()
                total_count = row[0]
            
            # Fetch rows
            query = f"""
                SELECT imap_uid, sender, subject, date, category, status 
                FROM emails 
                {where_clause} 
                ORDER BY imap_uid DESC 
                LIMIT ? OFFSET ?
            """
            row_params = params + [limit, offset]
            async with db.execute(query, row_params) as cursor:
                async for row in cursor:
                    emails.append({
                        "imap_uid": row["imap_uid"],
                        "sender": row["sender"],
                        "subject": row["subject"],
                        "date": row["date"],
                        "category": row["category"],
                        "status": row["status"]
                    })
                    
        return {
            "emails": emails,
            "total_count": total_count,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")

@router.post("/cleanup")
async def start_cleanup_endpoint(fast: bool = Query(True)):
    if sync_status.is_running:
        return {"status": "already_running"}
    await start_cleanup_task(fast=fast)
    return {"status": "cleanup_started"}

@router.get("/cleanup/preview")
async def cleanup_preview_endpoint():
    db_path = db_setup.DB_PATH
    if not os.path.exists(db_path):
        return {"total_count": 0, "breakdown": {}, "sample": []}
        
    try:
        now_utc = datetime.now(timezone.utc)
        matching_emails = []
        breakdown = {"Marketing": 0, "Social": 0, "Newsletter": 0}
        
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            db.row_factory = aiosqlite.Row
            query = "SELECT imap_uid, sender, subject, date, category FROM emails WHERE status = 'Pending'"
            async with db.execute(query) as cursor:
                async for row in cursor:
                    uid = row["imap_uid"]
                    sender = row["sender"]
                    subject = row["subject"]
                    date_str = row["date"]
                    category = row["category"]
                    
                    try:
                        dt = email.utils.parsedate_to_datetime(date_str)
                        if not dt.tzinfo:
                            dt = dt.replace(tzinfo=timezone.utc)
                        age = now_utc - dt
                    except Exception:
                        continue
                    
                    is_match = False
                    if category in ["Marketing", "Social"] and age.days > 30:
                        is_match = True
                    elif category == "Newsletter" and age.days > 14:
                        is_match = True
                        
                    if is_match:
                        matching_emails.append({
                            "imap_uid": uid,
                            "sender": sender,
                            "subject": subject,
                            "date": date_str,
                            "category": category,
                            "age_days": age.days
                        })
                        if category in breakdown:
                            breakdown[category] += 1
                        else:
                            breakdown[category] = 1
                            
        # Sort matching emails by UID descending (latest first) to show a sample
        matching_emails.sort(key=lambda x: x["imap_uid"], reverse=True)
        total_count = len(matching_emails)
        sample = matching_emails[:100]  # Return top 100 as sample
        
        return {
            "total_count": total_count,
            "breakdown": breakdown,
            "sample": sample
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@router.get("/senders")
async def get_senders_endpoint():
    db_path = db_setup.DB_PATH
    if not os.path.exists(db_path):
        return {"senders": []}
        
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            query = """
                SELECT sender, COUNT(*) as email_count 
                FROM emails 
                WHERE status = 'Pending' 
                GROUP BY sender 
                HAVING email_count > 0
                ORDER BY email_count DESC 
                LIMIT 15
            """
            senders = []
            async with db.execute(query) as cursor:
                async for row in cursor:
                    senders.append({
                        "sender": row[0],
                        "email_count": row[1]
                    })
            return {"senders": senders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")

class StageSenderRequest(BaseModel):
    sender: str

class StageSendersRequest(BaseModel):
    senders: list[str]

@router.post("/stage-sender")
async def stage_sender_endpoint(req: StageSenderRequest):
    await start_stage_sender(req.sender)
    return {"status": "staging_started"}

@router.post("/stage-senders")
async def stage_senders_endpoint(req: StageSendersRequest):
    await start_stage_senders(req.senders)
    return {"status": "staging_started"}

@router.post("/empty-trash")
async def empty_trash_endpoint():
    await start_empty_trash()
    return {"status": "empty_trash_started"}

class DeepPurgeRequest(BaseModel):
    sender: str

@router.post("/deep-purge")
async def deep_purge_endpoint(req: DeepPurgeRequest):
    await start_stage_sender(req.sender)
    return {"status": "deep_purge_started"}

class KeywordPurgeRequest(BaseModel):
    keyword: str
    segment: str = "all"

@router.post("/keyword-purge")
async def keyword_purge_endpoint(req: KeywordPurgeRequest):
    await start_keyword_purge(req.keyword, req.segment)
    return {"status": "keyword_purge_started"}

@router.get("/keyword-search")
async def keyword_search_endpoint(keyword: str = Query(...)):
    try:
        counts = await get_keyword_segment_counts(keyword)
        return {"counts": counts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



