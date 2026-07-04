"""
job_store.py — Async Job Queue for Long-Running GPU Tasks

Stores job state in memory (fast) and persists to SQLite so jobs survive
a container restart. Jobs are created when a long task is submitted and
updated as the task progresses.
"""

import asyncio
import logging
import os
import re
import sqlite3
import time
import uuid
from typing import Any, Optional

import aiosqlite

logger = logging.getLogger("spark.job_store")

# Path to the SQLite database that persists jobs
# Determine the output directory for job store.
# Uses the same logic as in main.py to locate the project-relative output folder.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_OUTPUT_DIR = os.getenv("OUTPUT_DIR", os.path.join(project_root, "output"))
_DB_PATH = os.path.join(_OUTPUT_DIR, "jobs.db")

# Status constants
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"


class JobStore:
    """
    Central job store for all async background tasks.
    In-memory dict for fast reads; persistent SQLite connection for storage.
    """
    MAX_CACHE_SIZE = 200

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._lock = asyncio.Lock()
        self._db: Optional[aiosqlite.Connection] = None
        self._initialised = False

    async def _ensure_init(self):
        if not self._initialised:
            os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
            self._db = await aiosqlite.connect(_DB_PATH)
            self._db.row_factory = aiosqlite.Row
            # WAL mode and timeouts configured once upon initialization
            await self._db.execute("PRAGMA journal_mode=WAL;")
            await self._db.execute("PRAGMA busy_timeout=5000;")
            
            await self._db.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id      TEXT PRIMARY KEY,
                    job_type    TEXT NOT NULL,
                    status      TEXT NOT NULL DEFAULT 'pending',
                    progress_pct INTEGER DEFAULT 0,
                    progress_msg TEXT DEFAULT '',
                    result      TEXT,
                    error       TEXT,
                    created_at  REAL NOT NULL,
                    updated_at  REAL NOT NULL
                )
            """)
            await self._db.commit()

            # Schema migration for new columns
            async with self._db.execute("PRAGMA table_info(jobs)") as cursor:
                columns = [row["name"] for row in await cursor.fetchall()]

            if "job_code" not in columns:
                await self._db.execute("ALTER TABLE jobs ADD COLUMN job_code TEXT;")
            if "content_type" not in columns:
                await self._db.execute("ALTER TABLE jobs ADD COLUMN content_type TEXT;")
            if "channel_id" not in columns:
                await self._db.execute("ALTER TABLE jobs ADD COLUMN channel_id INTEGER;")
            if "year_week" not in columns:
                await self._db.execute("ALTER TABLE jobs ADD COLUMN year_week TEXT;")
            if "parent_job_code" not in columns:
                await self._db.execute("ALTER TABLE jobs ADD COLUMN parent_job_code TEXT;")

            # Create UNIQUE index for job_code and index for year_week
            await self._db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_job_code ON jobs(job_code);")
            await self._db.execute("CREATE INDEX IF NOT EXISTS idx_jobs_year_week ON jobs(year_week);")
            await self._db.commit()
            
            await self._load_recent_from_db()
            self._initialised = True

    async def _load_recent_from_db(self):
        """Load the last 100 jobs from DB into memory cache on startup."""
        try:
            async with self._db.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 100"
            ) as cursor:
                async for row in cursor:
                    self._cache[row["job_id"]] = dict(row)
            logger.info(f"Loaded {len(self._cache)} recent jobs from DB")
        except Exception as e:
            logger.warning(f"Could not load jobs from DB: {e}")

    def _evict_cache(self):
        """Evict oldest updated entries if cache exceeds limit."""
        if len(self._cache) > self.MAX_CACHE_SIZE:
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k].get("updated_at", 0)
            )
            evict_count = len(self._cache) - self.MAX_CACHE_SIZE
            for key in sorted_keys[:evict_count]:
                self._cache.pop(key, None)

    async def create(
        self,
        job_type: str,
        job_code: Optional[str] = None,
        content_type: Optional[str] = None,
        channel_id: Optional[int] = None,
        year_week: Optional[str] = None,
        parent_job_code: Optional[str] = None,
    ) -> str:
        """Create a new job and return its job_id."""
        await self._ensure_init()
        job_id = f"{job_type[:8]}_{uuid.uuid4().hex[:8]}"
        now = time.time()
        # Auto‑generate job_code if not provided
        if not job_code:
            if not channel_id:
                raise ValueError("channel_id is required for job naming")
            if not content_type:
                raise ValueError("content_type is required for job naming")
            # Determine year_week if not provided (YYwWW)
            if not year_week:
                from datetime import datetime
                iso = datetime.utcnow().isocalendar()
                year = str(iso[0])[-2:]
                week = f"w{iso[1]:02d}"
                year_week = f"{year}{week}"
            # Get next sequence number for this channel/week/type
            seq = await self.get_next_sequence_number(channel_id, year_week, content_type)
            job_code = f"{channel_id}.{year_week}.{content_type}{seq:02d}"
        # Handle short job suffix if parent_job_code provided
        if parent_job_code and not job_code.endswith('.s'):
            async with self._db.execute(
                "SELECT job_code FROM jobs WHERE parent_job_code = ?",
                (parent_job_code,)
            ) as cursor:
                rows = await cursor.fetchall()
                existing = [r["job_code"] for r in rows]
            import re
            max_seq = 0
            for code in existing:
                m = re.search(r"\.s(\d+)$", code)
                if m:
                    max_seq = max(max_seq, int(m.group(1)))
            short_seq = max_seq + 1
            job_code = f"{parent_job_code}.s{short_seq:02d}"
        attempts = 0
        while True:
            try:
                await self._db.execute(
                    """INSERT INTO jobs (job_id, job_type, status, progress_pct, progress_msg,
                       result, error, created_at, updated_at, job_code, content_type, channel_id, year_week, parent_job_code)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (job_id, job_type, STATUS_PENDING, 0, "Queued...", None, None, now, now,
                     job_code, content_type, channel_id, year_week, parent_job_code),
                )
                await self._db.commit()
                break # success!
            except (sqlite3.IntegrityError, aiosqlite.IntegrityError) as e:
                if job_code:
                    # Parse and increment the job_code number
                    # Pattern matching shorts: e.g. 1.26w23.f01.s01 -> 1.26w23.f01.s02
                    match_short = re.match(r"^(\d+\.\d{2}w\d{2}\.[fd]\d{2})\.s(\d+)$", job_code)
                    if match_short:
                        parent_part = match_short.group(1)
                        seq = int(match_short.group(2)) + 1
                        job_code = f"{parent_part}.s{seq:02d}"
                    else:
                        match_main = re.match(r"^(\d+\.\d{2}w\d{2})\.([fd])(\d+)$", job_code)
                        if match_main:
                            prefix = match_main.group(1)
                            t = match_main.group(2)
                            seq = int(match_main.group(3)) + 1
                            job_code = f"{prefix}.{t}{seq:02d}"
                        else:
                            # If not matching standard pattern, append attempt count
                            job_code = f"{job_code}_{attempts}"
                    attempts += 1
                else:
                    # If duplicate on job_id, regenerate job_id and retry
                    job_id = f"{job_type[:8]}_{uuid.uuid4().hex[:8]}"
                    attempts += 1
            except Exception as e:
                logger.warning(f"Failed to persist job {job_id} to DB: {e}")
                break

        async with self._lock:
            self._cache[job_id] = job
            self._evict_cache()
            
        logger.info(f"Job created: {job_id} (type={job_type}, code={job_code})")
        return job_id

    async def update(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress_pct: Optional[int] = None,
        progress_msg: Optional[str] = None,
        result: Any = None,
        error: Optional[str] = None,
        job_code: Optional[str] = None,
        content_type: Optional[str] = None,
        channel_id: Optional[int] = None,
        year_week: Optional[str] = None,
        parent_job_code: Optional[str] = None,
    ):
        """Update a job's status, progress, or result."""
        await self._ensure_init()
        now = time.time()
        async with self._lock:
            job = self._cache.get(job_id)
            if not job:
                logger.warning(f"update() called for unknown job_id: {job_id}")
                return
            if status is not None:
                job["status"] = status
            if progress_pct is not None:
                job["progress_pct"] = progress_pct
            if progress_msg is not None:
                job["progress_msg"] = progress_msg
            if result is not None:
                job["result"] = result
            if error is not None:
                job["error"] = error
            if job_code is not None:
                job["job_code"] = job_code
            if content_type is not None:
                job["content_type"] = content_type
            if channel_id is not None:
                job["channel_id"] = channel_id
            if year_week is not None:
                job["year_week"] = year_week
            if parent_job_code is not None:
                job["parent_job_code"] = parent_job_code
            job["updated_at"] = now
            self._evict_cache()

        # Persist update to DB
        try:
            await self._db.execute(
                """UPDATE jobs SET status=?, progress_pct=?, progress_msg=?,
                   result=?, error=?, updated_at=?, job_code=?, content_type=?, channel_id=?, year_week=?, parent_job_code=?
                   WHERE job_id=?""",
                (
                    job["status"],
                    job["progress_pct"],
                    job["progress_msg"],
                    str(job["result"]) if job["result"] is not None else None,
                    job["error"],
                    now,
                    job.get("job_code"),
                    job.get("content_type"),
                    job.get("channel_id"),
                    job.get("year_week"),
                    job.get("parent_job_code"),
                    job_id,
                ),
            )
            await self._db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist job update {job_id}: {e}")

    async def complete(self, job_id: str, result: Any):
        """Mark a job as completed with its final result."""
        await self.update(
            job_id,
            status=STATUS_COMPLETED,
            progress_pct=100,
            progress_msg="Completed",
            result=result,
        )
        logger.info(f"Job completed: {job_id}")

    async def fail(self, job_id: str, error: str):
        """Mark a job as failed with an error message."""
        await self.update(
            job_id,
            status=STATUS_FAILED,
            progress_msg=f"Failed: {error}",
            error=error,
        )
        logger.error(f"Job failed: {job_id} — {error}")

    async def get(self, job_id: str) -> Optional[dict]:
        """Get a job by ID or Code. Returns None if not found."""
        await self._ensure_init()
        # Look in cache first
        job = self._cache.get(job_id)
        if job:
            return dict(job)
        # Search cache by job_code
        async with self._lock:
            for j in self._cache.values():
                if j.get("job_code") == job_id:
                    return dict(j)
        # Try DB
        try:
            async with self._db.execute(
                "SELECT * FROM jobs WHERE job_id = ? OR job_code = ?", (job_id, job_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    result = dict(row)
                    async with self._lock:
                        self._cache[result["job_id"]] = result
                        self._evict_cache()
                    return result
        except Exception as e:
            logger.warning(f"DB lookup failed for job {job_id}: {e}")
        return None

    async def get_next_sequence_number(self, channel_id: int, year_week: str, content_type: str) -> int:
        """Get the next sequence number for a given channel, week, and type."""
        await self._ensure_init()
        try:
            async with self._db.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE channel_id = ? AND year_week = ? AND content_type = ?",
                (channel_id, year_week, content_type)
            ) as cursor:
                row = await cursor.fetchone()
                count = row["count"] if row else 0
                return count + 1
        except Exception as e:
            logger.warning(f"Failed to calculate sequence number: {e}")
            return 1

    async def list_recent(self, limit: int = 50) -> list[dict]:
        """Return the most recent jobs, newest first."""
        await self._ensure_init()
        jobs = sorted(
            self._cache.values(), key=lambda j: j.get("created_at", 0), reverse=True
        )
        return [dict(j) for j in jobs[:limit]]

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending or running job. Returns True if cancelled."""
        await self._ensure_init()
        async with self._lock:
            job = self._cache.get(job_id)
            if not job:
                return False
            if job["status"] in (STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED):
                return False
            job["status"] = STATUS_CANCELLED
            job["progress_msg"] = "Cancelled by user"
            job["updated_at"] = time.time()
            self._evict_cache()
        try:
            await self._db.execute(
                "UPDATE jobs SET status=?, progress_msg=?, updated_at=? WHERE job_id=?",
                (STATUS_CANCELLED, "Cancelled by user", time.time(), job_id),
            )
            await self._db.commit()
        except Exception as e:
            logger.warning(f"Failed to persist cancellation for {job_id}: {e}")
        logger.info(f"Job cancelled: {job_id}")
        return True


# Singleton instance — import this in other modules
job_store = JobStore()
