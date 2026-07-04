"""
housekeeping.py — Operations runbook automated tasks (X07 Operations Runbook)

Cleans up temporary files, rotates/archives logs, prunes SQLite database,
and performs general host housekeeping.
"""

import os
import time
import sqlite3
import shutil
import logging
from typing import Dict, Any

logger = logging.getLogger("spark.housekeeping")

DB_PATH = os.path.join(os.getenv("OUTPUT_DIR", "/app/output"), "jobs.db")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "/app/output")

def prune_old_files(directory: str, max_age_days: int = 7) -> int:
    """Deletes files in the target directory that are older than max_age_days."""
    if not os.path.exists(directory):
        return 0
        
    now = time.time()
    cutoff = now - (max_age_days * 86400)
    deleted_count = 0
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        # Avoid deleting database itself or directories we care about
        if filename == "jobs.db" or os.path.isdir(filepath):
            continue
            
        try:
            mtime = os.path.getmtime(filepath)
            if mtime < cutoff:
                os.remove(filepath)
                deleted_count += 1
        except Exception as e:
            logger.error(f"Failed to delete {filepath}: {e}")
            
    return deleted_count

def prune_jobs_database(max_age_days: int = 30) -> Dict[str, Any]:
    """Deletes job records older than max_age_days and runs VACUUM on the database."""
    if not os.path.exists(DB_PATH):
        return {"status": "skipped", "message": "Database file not found"}
        
    now = time.time()
    cutoff = now - (max_age_days * 86400)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE created_at < ?", (cutoff,))
        to_delete = cursor.fetchone()[0]
        
        cursor.execute("DELETE FROM jobs WHERE created_at < ?", (cutoff,))
        conn.commit()
        
        # Free up unused space
        cursor.execute("VACUUM")
        conn.close()
        
        return {
            "status": "success",
            "records_deleted": to_delete,
            "message": f"Successfully deleted {to_delete} old job records and optimized database."
        }
    except Exception as e:
        logger.error(f"Database pruning failed: {e}")
        return {"status": "error", "message": str(e)}

def check_disk_space(path: str = "/") -> Dict[str, Any]:
    """Returns disk space usage statistics."""
    try:
        total, used, free = shutil.disk_usage(path)
        percent_used = (used / total) * 100
        return {
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent_used": round(percent_used, 1),
            "warning": percent_used > 90.0
        }
    except Exception as e:
        return {"error": str(e)}

def run_housekeeping(max_file_age_days: int = 7, max_db_age_days: int = 30) -> Dict[str, Any]:
    """Runs all housekeeping tasks and logs outcomes."""
    logger.info("Starting automated housekeeping loop...")
    files_deleted = prune_old_files(OUTPUT_DIR, max_file_age_days)
    db_result = prune_jobs_database(max_db_age_days)
    disk_stats = check_disk_space(OUTPUT_DIR)
    
    report = {
        "timestamp": time.time(),
        "files_pruned": files_deleted,
        "database_pruning": db_result,
        "disk_space": disk_stats
    }
    
    logger.info(f"Housekeeping complete: Pruned {files_deleted} files. Disk usage is {disk_stats.get('percent_used')}%")
    return report
