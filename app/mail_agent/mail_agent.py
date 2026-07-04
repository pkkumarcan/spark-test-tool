import os
import asyncio
import logging
import imaplib
import email
from email.header import decode_header
import time
import aiosqlite
import re
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone, timedelta
import httpx
from app.mail_agent import db_setup

logger = logging.getLogger("spark.mail_agent")

# Global Status Singleton
class MailSyncStatus:
    def __init__(self):
        self.is_running = False
        self.total_emails = 0
        self.synced_emails = 0
        self.current_speed = 0.0  # UIDs per second
        self.status = "Stopped"   # "Syncing", "Stopped", "Completed", "Error", "Purging"
        self.logs = []
        self.error_message = None
        self.purge_queue = []     # List of sender emails currently in the queue
        self.purging_senders = {} # Dict: sender_email -> status ("Queued", "Purging...", "Done", "Error")

    def log(self, message: str):
        timestamp = time.strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        logger.info(message)
        self.logs.append(log_line)
        if len(self.logs) > 500:
            self.logs.pop(0)

    def reset_speed(self):
        self.current_speed = 0.0

sync_status = MailSyncStatus()
_active_sync_tasks = set()

_purge_queue = asyncio.Queue()
_purge_workers = []
_purge_workers_running = False
BACKOFF_INTERVALS = [5, 10, 20]



# Helper to decode email header safely
def safe_decode(header_value):
    if not header_value:
        return ""
    try:
        decoded_fragments = decode_header(header_value)
        parts = []
        for text, encoding in decoded_fragments:
            if isinstance(text, bytes):
                try:
                    parts.append(text.decode(encoding or "utf-8", errors="ignore"))
                except Exception:
                    parts.append(text.decode("latin1", errors="ignore"))
            else:
                parts.append(text)
        return "".join(parts).strip()
    except Exception:
        return str(header_value)

def classify_heuristic(sender, subject):
    sender_lower = (sender or "").lower()
    subj_lower = (subject or "").lower()
    
    # Social heuristics
    social_domains = [
        "facebook", "linkedin", "twitter", "instagram", "youtube", "pinterest", 
        "social", "friend", "follow", "connect", "network", "tumblr", "tiktok", "reddit"
    ]
    if any(dom in sender_lower for dom in social_domains) or any(k in subj_lower for k in ["linkedin", "facebook", "friend request"]):
        return "Social"
        
    # Newsletter heuristics
    newsletter_keywords = [
        "newsletter", "digest", "weekly", "daily", "bulletin", "substack", "medium.com", 
        "news", "brief", "read", "update", "dispatch", "inside"
    ]
    if any(k in sender_lower for k in newsletter_keywords) or any(k in subj_lower for k in ["newsletter", "daily digest", "weekly digest", "bulletin"]):
        return "Newsletter"
        
    # Marketing heuristics
    marketing_keywords = [
        "marketing", "promo", "deal", "offer", "shop", "store", "sales", "discount", 
        "coupon", "subscribe", "campaign", "alert", "notification", "billing", "receipt",
        "invoice", "no-reply", "noreply", "info@", "bounce", "alert", "support", "orders"
    ]
    if any(k in sender_lower for k in marketing_keywords) or any(k in subj_lower for k in ["off", "deal", "discount", "free", "save", "sale", "order", "invoice", "receipt", "alert"]):
        return "Marketing"
        
    return "Inbox"

async def classify_existing_emails(db_path):
    async with aiosqlite.connect(db_path) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        async with db.execute("SELECT imap_uid, sender, subject FROM emails WHERE category = 'Pending'") as cursor:
            rows = await cursor.fetchall()
        
        if not rows:
            return
            
        updates = []
        for uid, sender, subject in rows:
            cat = classify_heuristic(sender, subject)
            updates.append((cat, uid))
            
        await db.executemany("UPDATE emails SET category = ? WHERE imap_uid = ?", updates)
        await db.commit()

# Blocking IMAP sync operations executed in thread pool
def connect_imap(email_addr, app_password):
    try:
        host = os.getenv("YAHOO_IMAP_SERVER", "export.imap.mail.yahoo.com")
        logger.info(f"Connecting to Yahoo IMAP at {host}...")
        imap = imaplib.IMAP4_SSL(host, 993, timeout=30)
        imap.login(email_addr, app_password)
        return imap
    except Exception as e:
        raise Exception(f"IMAP connection failed: {e}")

def fetch_uids_list(imap, folder_name="INBOX", segment="all"):
    status, select_data = imap.select(folder_name)
    if status != "OK":
        raise Exception(f"Failed to select folder {folder_name}: {select_data}")
    
    total_messages = 0
    if select_data and select_data[0]:
        try:
            total_messages = int(select_data[0])
        except ValueError:
            pass
            
    logger.info(f"Total messages in {folder_name}: {total_messages}")
    
    if segment != "all":
        criteria = []
        if segment == "2007-2012":
            criteria = ['SINCE', '01-Jan-2007', 'BEFORE', '01-Jan-2013']
        elif segment == "2013-2017":
            criteria = ['SINCE', '01-Jan-2013', 'BEFORE', '01-Jan-2018']
        elif segment == "2018-2022":
            criteria = ['SINCE', '01-Jan-2018', 'BEFORE', '01-Jan-2023']
        elif segment == "2023-2026":
            criteria = ['SINCE', '01-Jan-2023', 'BEFORE', '01-Jan-2027']
        
        logger.info(f"Performing date-segmented search in {folder_name} using criteria: {criteria}")
        status, data = imap.uid("search", None, *criteria)
        if status != "OK":
            raise Exception(f"Failed to search folder {folder_name} with criteria {criteria}: {data}")
        
        uids = []
        if data and data[0]:
            uids = [int(uid) for uid in data[0].split()]
        return uids

    uids = []
    if total_messages == 0:
        return uids
        
    chunk_size = 10000
    for start in range(1, total_messages + 1, chunk_size):
        end = min(start + chunk_size - 1, total_messages)
        range_str = f"{start}:{end}"
        logger.info(f"Fetching UID sequence range {range_str}...")
        status, data = imap.fetch(range_str, "(UID)")
        if status != "OK":
            raise Exception(f"Failed to fetch UIDs for sequence range {range_str}: {data}")
            
        for item in data:
            if isinstance(item, tuple):
                text = item[0].decode("utf-8", errors="ignore")
            elif isinstance(item, bytes):
                text = item.decode("utf-8", errors="ignore")
            else:
                continue
                
            uid_match = re.search(r"\bUID\s+(\d+)\b", text, re.IGNORECASE)
            if uid_match:
                uids.append(int(uid_match.group(1)))
                
    return uids

def fetch_headers_batch(imap, uid_batch):
    # uid_batch is a list of UIDs
    uid_str = ",".join(str(uid) for uid in uid_batch)
    status, data = imap.uid("fetch", uid_str, "(BODY[HEADER.FIELDS (SUBJECT FROM DATE)])")
    if status != "OK":
        raise Exception(f"Batch fetch failed: {data}")
    
    results = []
    # Parse results
    current_uid = None
    for item in data:
        if isinstance(item, tuple):
            # Header line looks like: (b'118 (UID 54321 BODY[HEADER... ] {123}', b'From: ...')
            header_meta = item[0].decode("utf-8", errors="ignore")
            # Extract UID using regex
            uid_match = re.search(r"\bUID\s+(\d+)\b", header_meta, re.IGNORECASE)
            if not uid_match:
                uid_match = re.search(r"UID\s+(\d+)", header_meta, re.IGNORECASE)
            if not uid_match:
                continue
            uid = int(uid_match.group(1))
            
            raw_headers = item[1].decode("utf-8", errors="ignore")
            msg = email.message_from_string(raw_headers)
            
            sender = safe_decode(msg.get("From"))
            subject = safe_decode(msg.get("Subject"))
            date = safe_decode(msg.get("Date"))
            
            results.append({
                "imap_uid": uid,
                "sender": sender,
                "subject": subject,
                "date": date
            })
            
    return results

async def get_imap_folders_task():
    email_addr = os.getenv("YAHOO_EMAIL")
    app_password = os.getenv("YAHOO_APP_PASSWORD")
    if not email_addr or not app_password:
        raise Exception("Credentials missing in .env")
    return await asyncio.to_thread(_get_imap_folders_sync, email_addr, app_password)

def _get_imap_folders_sync(email_addr, app_password):
    imap = connect_imap(email_addr, app_password)
    try:
        status, folder_list = imap.list()
        if status != "OK":
            raise Exception(f"Failed to list folders: {folder_list}")
        
        folders = []
        for f in folder_list:
            line = f.decode("utf-8", errors="ignore")
            # Parse folder list, e.g., (\HasNoChildren) "/" "INBOX"
            match = re.search(r'\(([^)]*)\)\s+"([^"]+)"\s+(.+)$', line)
            if match:
                folder_name = match.group(3).strip()
                if folder_name.startswith('"') and folder_name.endswith('"'):
                    folder_name = folder_name[1:-1]
                folders.append(folder_name)
            else:
                match_nil = re.search(r'\(([^)]*)\)\s+NIL\s+(.+)$', line)
                if match_nil:
                    folder_name = match_nil.group(2).strip()
                    if folder_name.startswith('"') and folder_name.endswith('"'):
                        folder_name = folder_name[1:-1]
                    folders.append(folder_name)
                else:
                    parts = line.split('"/"')
                    if len(parts) >= 2:
                        folder_name = parts[-1].strip()
                        if folder_name.startswith('"') and folder_name.endswith('"'):
                            folder_name = folder_name[1:-1]
                        folders.append(folder_name)
                    else:
                        folders.append(line)
        return folders
    finally:
        try:
            imap.logout()
        except Exception:
            pass

async def start_sync_task(folder_name="INBOX", segment="all"):
    if sync_status.is_running:
        return
    
    # Initialize DB schema
    db_setup.init_db()
    
    # Run classification on existing pending records in the background
    asyncio.create_task(classify_existing_emails(db_setup.DB_PATH))
    
    sync_status.is_running = True
    sync_status.status = "Syncing"
    sync_status.error_message = None
    sync_status.log(f"Starting Yahoo Mail Organizer sync ({folder_name} - {segment})...")

    # Load credentials
    email_addr = os.getenv("YAHOO_EMAIL")
    app_password = os.getenv("YAHOO_APP_PASSWORD")

    if not email_addr or not app_password:
        sync_status.is_running = False
        sync_status.status = "Error"
        sync_status.error_message = "Credentials missing in .env"
        sync_status.log("[ERROR] Yahoo credentials missing in .env file.")
        return

    # Start loop
    task = asyncio.create_task(run_sync_loop(email_addr, app_password, folder_name, segment))
    _active_sync_tasks.add(task)
    task.add_done_callback(_active_sync_tasks.discard)

async def run_sync_loop(email_addr, app_password, folder_name="INBOX", segment="all"):
    imap = None
    try:
        # Step 1: Connect
        sync_status.log("Connecting to Yahoo Mail IMAP...")
        imap = await asyncio.to_thread(connect_imap, email_addr, app_password)
        sync_status.log("Connected and authenticated successfully.")

        # Step 2: Fetch UIDs
        sync_status.log(f"Retrieving list of UIDs from {folder_name} ({segment})...")
        all_uids = await asyncio.to_thread(fetch_uids_list, imap, folder_name, segment)
        sync_status.total_emails = len(all_uids)
        sync_status.log(f"Found {sync_status.total_emails:,} messages matching criteria in {folder_name}.")

        # Step 3: Check SQLite for synced UIDs to support resume
        sync_status.log("Reading state from local SQLite database...")
        db_path = db_setup.DB_PATH
        synced_uids = set()
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            async with db.execute("SELECT imap_uid FROM emails") as cursor:
                async for row in cursor:
                    synced_uids.add(row[0])
        
        sync_status.synced_emails = len(synced_uids)
        sync_status.log(f"SQLite database contains {sync_status.synced_emails:,} already synced headers.")

        # Filter UIDs we need to fetch
        pending_uids = [uid for uid in all_uids if uid not in synced_uids]
        # Sort pending UIDs ascending (oldest first to preserve chronological load)
        pending_uids.sort()
        
        if not pending_uids:
            sync_status.log("All email headers matching criteria are already synced.")
            sync_status.status = "Completed"
            sync_status.is_running = False
            return

        sync_status.log(f"Preparing to sync {len(pending_uids):,} pending headers...")

        # Step 4: Batch fetch headers
        batch_size = 2000
        total_batches = (len(pending_uids) + batch_size - 1) // batch_size
        
        start_time = time.time()
        last_speed_time = start_time
        last_speed_count = sync_status.synced_emails

        for i in range(total_batches):
            if not sync_status.is_running:
                sync_status.log("Sync paused by user.")
                break

            batch = pending_uids[i * batch_size : (i + 1) * batch_size]
            sync_status.log(f"Syncing batch {i+1}/{total_batches} ({len(batch)} headers)...")

            success = False
            retries = 3
            fetched_emails = []

            while retries > 0 and not success:
                try:
                    fetched_emails = await asyncio.to_thread(fetch_headers_batch, imap, batch)
                    success = True
                except Exception as e:
                    retries -= 1
                    sync_status.log(f"[WARNING] Batch fetch failed: {e}. Retries remaining: {retries}")
                    if retries > 0:
                        await asyncio.sleep(2)
                        # Reconnect
                        try:
                            if imap:
                                try:
                                    await asyncio.to_thread(imap.logout)
                                except Exception:
                                    pass
                            imap = await asyncio.to_thread(connect_imap, email_addr, app_password)
                            await asyncio.to_thread(imap.select, folder_name)
                        except Exception as re_err:
                            sync_status.log(f"[WARNING] Reconnection failed: {re_err}")

            if not success:
                raise Exception("IMAP connection lost after multiple retries. Halting sync.")

            # Save batch to SQLite
            if fetched_emails:
                async with aiosqlite.connect(db_path) as db:
                    await db.execute("PRAGMA journal_mode=WAL;")
                    for em in fetched_emails:
                        cat = classify_heuristic(em["sender"], em["subject"])
                        await db.execute("""
                            INSERT OR IGNORE INTO emails (imap_uid, sender, subject, date, category, status)
                            VALUES (?, ?, ?, ?, ?, 'Pending')
                        """, (em["imap_uid"], em["sender"], em["subject"], em["date"], cat))
                    await db.commit()

            # Update status
            sync_status.synced_emails += len(batch)
            
            # Calculate Speed (UIDs / second)
            now = time.time()
            elapsed_interval = now - last_speed_time
            if elapsed_interval >= 1.0:
                count_diff = sync_status.synced_emails - last_speed_count
                sync_status.current_speed = count_diff / elapsed_interval
                last_speed_count = sync_status.synced_emails
                last_speed_time = now

            await asyncio.sleep(0.1)

        if sync_status.is_running:
            sync_status.log("Inbox database sync completed successfully!")
            sync_status.status = "Completed"
            sync_status.is_running = False

    except Exception as e:
        sync_status.log(f"[ERROR] Sync crashed: {e}")
        sync_status.status = "Error"
        sync_status.error_message = str(e)
        sync_status.is_running = False
    finally:
        sync_status.reset_speed()
        if imap:
            try:
                await asyncio.to_thread(imap.logout)
            except Exception:
                pass

def stop_sync():
    if sync_status.is_running:
        sync_status.is_running = False
        sync_status.status = "Stopped"
        sync_status.log("Inbox sync stopped by user request.")

def parse_list_unsubscribe(header_value):
    """
    Parses a List-Unsubscribe header which looks like:
    <mailto:unsubscribe@example.com?subject=unsubscribe-id>, <https://example.com/unsub>
    Returns a dict with 'mailto' (dict or None) and 'http' (str or None)
    """
    if not header_value:
        return {}
        
    result = {}
    # Split by comma to handle multiple links
    parts = header_value.split(",")
    for part in parts:
        part = part.strip()
        if part.startswith("<") and part.endswith(">"):
            url = part[1:-1].strip()
            if url.startswith("mailto:"):
                # Parse mailto
                parsed = urllib.parse.urlparse(url)
                to_addr = parsed.path
                query = urllib.parse.parse_qs(parsed.query)
                subject = query.get("subject", ["Unsubscribe"])[0]
                body = query.get("body", ["Unsubscribe"])[0]
                result["mailto"] = {
                    "to": to_addr,
                    "subject": subject,
                    "body": body
                }
            elif url.startswith("http://") or url.startswith("https://"):
                result["http"] = url
    return result

def send_smtp_unsubscribe(email_addr, app_password, to_addr, subject, body="Unsubscribe"):
    try:
        msg = MIMEText(body)
        msg["From"] = email_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        
        with smtplib.SMTP_SSL("smtp.mail.yahoo.com", 465, timeout=15) as server:
            server.login(email_addr, app_password)
            server.send_message(msg)
        return True
    except Exception as e:
        logger.error(f"SMTP unsubscribe failed: {e}")
        return False

async def trigger_http_unsubscribe(url, has_post_header=False):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if has_post_header:
                r = await client.post(url, data={"List-Unsubscribe": "One-Click"})
            else:
                r = await client.get(url)
            return r.status_code in [200, 201, 202, 204]
    except Exception as e:
        logger.error(f"HTTP unsubscribe failed: {e}")
        return False

async def start_cleanup_task(fast: bool = True):
    if sync_status.is_running:
        return
        
    sync_status.is_running = True
    sync_status.status = "Cleaning"
    sync_status.error_message = None
    sync_status.log(f"Starting Yahoo Mail Organizer bulk cleanup (Fast Mode: {fast})...")
    
    email_addr = os.getenv("YAHOO_EMAIL")
    app_password = os.getenv("YAHOO_APP_PASSWORD")
    
    if not email_addr or not app_password:
        sync_status.is_running = False
        sync_status.status = "Error"
        sync_status.error_message = "Credentials missing in .env"
        sync_status.log("[ERROR] Yahoo credentials missing in .env file.")
        return
        
    task = asyncio.create_task(run_cleanup_loop(email_addr, app_password, fast=fast))
    _active_sync_tasks.add(task)
    task.add_done_callback(_active_sync_tasks.discard)

async def run_cleanup_loop(email_addr, app_password, fast: bool = True):
    imap = None
    db_conn = None
    try:
        db_path = db_setup.DB_PATH
        db_conn = await aiosqlite.connect(db_path)
        await db_conn.execute("PRAGMA journal_mode=WAL;")
        await db_conn.execute("PRAGMA synchronous=NORMAL;")
        
        # Step 1: Run classification migration for pending
        sync_status.log("Ensuring database records are classified...")
        await classify_existing_emails(db_path)
        
        # Step 2: Fetch active pending emails
        sync_status.log("Identifying emails exceeding Time-To-Live (TTL)...")
        now_utc = datetime.now(timezone.utc)
        flagged_uids = []
        
        async with db_conn.execute("SELECT imap_uid, sender, subject, date, category FROM emails WHERE status = 'Pending'") as cursor:
            async for row in cursor:
                uid, sender, subject, date_str, category = row
                try:
                    dt = email.utils.parsedate_to_datetime(date_str)
                    if not dt.tzinfo:
                        dt = dt.replace(tzinfo=timezone.utc)
                    age = now_utc - dt
                except Exception:
                    continue
                
                if category in ["Marketing", "Social"] and age.days > 30:
                    flagged_uids.append(uid)
                elif category == "Newsletter" and age.days > 14:
                    flagged_uids.append(uid)
                        
        total_flagged = len(flagged_uids)
        if total_flagged == 0:
            sync_status.log("No TTL-expired clutter found to clean up.")
            sync_status.status = "Completed"
            sync_status.is_running = False
            return
            
        sync_status.log(f"Found {total_flagged:,} expired emails to clean up.")
        
        # Connect to IMAP
        sync_status.log("Connecting to Yahoo IMAP for cleanup...")
        imap = await asyncio.to_thread(connect_imap, email_addr, app_password)
        
        # Re-select INBOX to prepare for operations
        await asyncio.to_thread(imap.select, "INBOX")
        
        # Track unsubscribed senders to avoid multiple triggers per sender
        unsubscribed_senders = set()
        
        # Process in batches
        batch_size = 1000 if fast else 500
        total_batches = (total_flagged + batch_size - 1) // batch_size
        
        for i in range(total_batches):
            if not sync_status.is_running:
                sync_status.log("Cleanup paused by user.")
                break
                
            batch_uids = flagged_uids[i * batch_size : (i + 1) * batch_size]
            sync_status.log(f"Processing batch {i+1}/{total_batches} ({len(batch_uids)} emails)...")
            
            uid_str = ",".join(str(uid) for uid in batch_uids)
            
            if not fast:
                # Fetch List-Unsubscribe headers
                success = False
                retries = 3
                unsub_data = []
                
                while retries > 0 and not success:
                    try:
                        status, unsub_data = await asyncio.to_thread(
                            imap.uid, "fetch", uid_str, "(BODY[HEADER.FIELDS (List-Unsubscribe List-Unsubscribe-Post From)])"
                        )
                        if status == "OK":
                            success = True
                        else:
                            raise Exception(f"IMAP returned: {status}")
                    except Exception as e:
                        retries -= 1
                        sync_status.log(f"[WARNING] Unsubscribe headers fetch failed: {e}. Retries remaining: {retries}")
                        if retries > 0:
                            await asyncio.sleep(2)
                            try:
                                if imap:
                                    try:
                                        await asyncio.to_thread(imap.logout)
                                    except Exception:
                                        pass
                                imap = await asyncio.to_thread(connect_imap, email_addr, app_password)
                                await asyncio.to_thread(imap.select, "INBOX")
                            except Exception as re_err:
                                sync_status.log(f"[WARNING] Reconnection failed: {re_err}")
                                
                if not success:
                    raise Exception("IMAP connection lost during header fetch. Halting cleanup.")
                    
                # Parse List-Unsubscribe headers and trigger unsubscriptions
                parsed_headers = {}
                for item in unsub_data:
                    if isinstance(item, tuple):
                        header_meta = item[0].decode("utf-8", errors="ignore")
                        uid_match = re.search(r"UID\s+(\d+)", header_meta, re.IGNORECASE)
                        if not uid_match:
                            continue
                        uid = int(uid_match.group(1))
                        
                        raw_headers = item[1].decode("utf-8", errors="ignore")
                        msg = email.message_from_string(raw_headers)
                        parsed_headers[uid] = msg
                
                # Define async helper for unsubscribe
                async def process_unsubscribe(sender_email, msg):
                    unsub_header = msg.get("List-Unsubscribe")
                    post_header = msg.get("List-Unsubscribe-Post")
                    if not unsub_header:
                        return
                        
                    unsub_actions = parse_list_unsubscribe(unsub_header)
                    has_post = post_header and "One-Click" in post_header
                    
                    triggered = False
                    # Try HTTP first
                    if "http" in unsub_actions:
                        url = unsub_actions["http"]
                        sync_status.log(f"Unsubscribing {sender_email} via HTTP GET...")
                        http_ok = await trigger_http_unsubscribe(url, has_post_header=has_post)
                        if http_ok:
                            sync_status.log(f"HTTP unsubscribe succeeded for {sender_email}")
                            triggered = True
                        else:
                            sync_status.log(f"[WARNING] HTTP unsubscribe failed or returned error for {sender_email}")
                            
                    # Try mailto if HTTP not present or failed
                    if not triggered and "mailto" in unsub_actions:
                        to_info = unsub_actions["mailto"]
                        sync_status.log(f"Sending SMTP unsubscribe email to {to_info['to']} for {sender_email}...")
                        smtp_ok = await asyncio.to_thread(
                            send_smtp_unsubscribe,
                            email_addr,
                            app_password,
                            to_info["to"],
                            to_info["subject"],
                            to_info["body"]
                        )
                        if smtp_ok:
                            sync_status.log(f"SMTP unsubscribe sent for {sender_email}")
                            triggered = True
                        else:
                            sync_status.log(f"[WARNING] SMTP unsubscribe email failed to send for {sender_email}")

                # Go through emails in batch and trigger unsubscribe concurrently
                unsub_tasks = []
                seen_batch_senders = set()
                for uid in batch_uids:
                    msg = parsed_headers.get(uid)
                    if not msg:
                        continue
                        
                    sender = safe_decode(msg.get("From"))
                    sender_email = ""
                    # Extract clean email address
                    if "<" in sender and ">" in sender:
                        sender_email = sender.split("<")[1].split(">")[0].strip().lower()
                    else:
                        sender_email = sender.strip().lower()
                        
                    if sender_email and sender_email not in unsubscribed_senders and sender_email not in seen_batch_senders:
                        seen_batch_senders.add(sender_email)
                        unsubscribed_senders.add(sender_email)
                        unsub_tasks.append(process_unsubscribe(sender_email, msg))
                        
                if unsub_tasks:
                    await asyncio.gather(*unsub_tasks)
                                
            # Store \Deleted flag directly on INBOX
            success = False
            retries = 3
            while retries > 0 and not success:
                try:
                    status, res_data = await asyncio.to_thread(imap.uid, "store", uid_str, "+FLAGS", "(\\Deleted)")
                    if status == "OK":
                        success = True
                    else:
                        raise Exception(f"Store flag failed: {status}")
                except Exception as e:
                    retries -= 1
                    sync_status.log(f"[WARNING] Batch flag failed: {e}. Retries remaining: {retries}")
                    if retries > 0:
                        await asyncio.sleep(2)
                        try:
                            if imap:
                                try:
                                    await asyncio.to_thread(imap.logout)
                                except Exception:
                                    pass
                            imap = await asyncio.to_thread(connect_imap, email_addr, app_password)
                            await asyncio.to_thread(imap.select, "INBOX")
                        except Exception as re_err:
                            sync_status.log(f"[WARNING] Reconnection failed: {re_err}")
                            
            if not success:
                raise Exception("IMAP connection lost during flagging. Halting cleanup.")
                
            # Update SQLite only on successful STORE
            # Parameterised query — avoids SQL injection (never use f-strings for SQL)
            placeholders = ",".join("?" * len(batch_uids))
            await db_conn.execute(
                f"UPDATE emails SET status = 'Deleted' WHERE imap_uid IN ({placeholders})",
                batch_uids
            )
            await db_conn.commit()
                
            sync_status.log(f"Flagged {len(batch_uids)} emails as Deleted.")
            await asyncio.sleep(0.05)
            
        # Expunge once at the end of cleanup
        if sync_status.is_running:
            sync_status.log("Expunging deleted clutter from INBOX...")
            await asyncio.to_thread(imap.expunge)
            
        if sync_status.is_running:
            sync_status.log("Clutter cleanup completed successfully!")
            sync_status.status = "Completed"
            sync_status.is_running = False
            
    except Exception as e:
        sync_status.log(f"[ERROR] Cleanup crashed: {e}")
        sync_status.status = "Error"
        sync_status.error_message = str(e)
        sync_status.is_running = False
    finally:
        if db_conn:
            try:
                await db_conn.close()
            except Exception:
                pass
        if imap:
            try:
                await asyncio.to_thread(imap.logout)
            except Exception:
                pass

async def start_stage_senders(senders: list[str]):
    # Add to queue
    for sender in senders:
        job_key = f"sender:{sender}"
        if job_key not in sync_status.purge_queue:
            sync_status.purge_queue.append(job_key)
            sync_status.purging_senders[job_key] = "Queued"
            await _purge_queue.put({"type": "sender", "target": sender, "key": job_key})
            sync_status.log(f"Queued sender for purge: {sender}")
            
    # Ensure workers are running
    global _purge_workers_running, _purge_workers
    if not _purge_workers_running:
        _purge_workers_running = True
        sync_status.is_running = True
        sync_status.status = "Purging"
        sync_status.error_message = None
        
        # Start 3 background worker tasks
        _purge_workers = []
        for i in range(3):
            task = asyncio.create_task(purge_worker_task(i + 1))
            _active_sync_tasks.add(task)
            task.add_done_callback(_active_sync_tasks.discard)
            _purge_workers.append(task)

async def start_stage_sender(sender: str):
    await start_stage_senders([sender])

async def get_keyword_segment_counts(keyword: str):
    email_addr = os.getenv("YAHOO_EMAIL")
    app_password = os.getenv("YAHOO_APP_PASSWORD")
    if not email_addr or not app_password:
        raise Exception("Credentials missing in .env")
    return await asyncio.to_thread(_get_keyword_segment_counts_sync, email_addr, app_password, keyword)

def _get_keyword_segment_counts_sync(email_addr, app_password, keyword):
    imap = connect_imap(email_addr, app_password)
    try:
        status, select_data = imap.select("INBOX")
        if status != "OK":
            raise Exception(f"Failed to select INBOX: {select_data}")
        
        segments = {
            "2007-2012": ['TEXT', f'"{keyword}"', 'SINCE', '01-Jan-2007', 'BEFORE', '01-Jan-2013'],
            "2013-2017": ['TEXT', f'"{keyword}"', 'SINCE', '01-Jan-2013', 'BEFORE', '01-Jan-2018'],
            "2018-2022": ['TEXT', f'"{keyword}"', 'SINCE', '01-Jan-2018', 'BEFORE', '01-Jan-2023'],
            "2023-2027": ['TEXT', f'"{keyword}"', 'SINCE', '01-Jan-2023', 'BEFORE', '01-Jan-2028']
        }
        
        results = {}
        for seg_name, criteria in segments.items():
            status, data = imap.uid("search", None, *criteria)
            count = 0
            if status == "OK" and data and data[0]:
                count = len(data[0].split())
            results[seg_name] = count
            
        return results
    finally:
        try:
            imap.logout()
        except Exception:
            pass

async def start_keyword_purge(keyword: str, segment: str = "all"):
    job_key = f"keyword:{keyword}:{segment}"
    if job_key not in sync_status.purge_queue:
        sync_status.purge_queue.append(job_key)
        sync_status.purging_senders[job_key] = "Queued"
        await _purge_queue.put({"type": "keyword", "target": keyword, "segment": segment, "key": job_key})
        sync_status.log(f"Queued keyword for purge: {keyword} ({segment})")
        
    # Ensure workers are running
    global _purge_workers_running, _purge_workers
    if not _purge_workers_running:
        _purge_workers_running = True
        sync_status.is_running = True
        sync_status.status = "Purging"
        sync_status.error_message = None
        
        # Start 3 background worker tasks
        _purge_workers = []
        for i in range(3):
            task = asyncio.create_task(purge_worker_task(i + 1))
            _active_sync_tasks.add(task)
            task.add_done_callback(_active_sync_tasks.discard)
            _purge_workers.append(task)

async def process_flagging_batch(mail, batch_uids):
    uid_string = ",".join(batch_uids)
    
    # 1. Apply \Deleted flag directly
    status, data = await asyncio.to_thread(mail.uid, 'store', uid_string, '+FLAGS', '(\\Deleted)')
    
    # 2. Transaction Atomicity: Only update SQLite if Yahoo returns OK
    if status == 'OK':
        db_path = db_setup.DB_PATH
        async with aiosqlite.connect(db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute(f"UPDATE emails SET status = 'Deleted' WHERE imap_uid IN ({uid_string})")
            await db.commit()
    else:
        raise Exception(f"Yahoo rejected STORE command: {data}")

async def purge_worker_task(worker_id: int):
    email_addr = os.getenv("YAHOO_EMAIL")
    app_password = os.getenv("YAHOO_APP_PASSWORD")
    
    if not email_addr or not app_password:
        sync_status.log(f"[Worker {worker_id}] [ERROR] Yahoo credentials missing in .env")
        return

    mail = None
    
    try:
        while True:
            # Safely check if we have jobs left
            if len(sync_status.purge_queue) == 0:
                break
                
            try:
                job = _purge_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            job_key = job["key"]
            job_type = job["type"]
            target = job["target"]
            segment = job.get("segment", "all")

            sync_status.purging_senders[job_key] = "Purging..."
            sync_status.log(f"[Worker {worker_id}] Dequeued job: {job_key}")
            
            # Connection and selection logic with backoff
            retries = 0
            while mail is None:
                try:
                    sync_status.log(f"[Worker {worker_id}] Connecting to Yahoo IMAP...")
                    mail = await asyncio.to_thread(connect_imap, email_addr, app_password)
                    await asyncio.to_thread(mail.select, "INBOX")
                    sync_status.log(f"[Worker {worker_id}] Connected and selected INBOX.")
                    break
                except Exception as e:
                    if retries < len(BACKOFF_INTERVALS):
                        sleep_time = BACKOFF_INTERVALS[retries]
                        sync_status.log(f"[Worker {worker_id}] Connection failed: {e}. Retrying in {sleep_time}s...")
                        await asyncio.sleep(sleep_time)
                        retries += 1
                    else:
                        sync_status.log(f"[Worker {worker_id}] [ERROR] Fatal connection error. Skipping {job_key}.")
                        sync_status.purging_senders[job_key] = "Error"
                        if job_key in sync_status.purge_queue:
                            sync_status.purge_queue.remove(job_key)
                        _purge_queue.task_done()
                        break
            
            if mail is None:
                continue
                
            # Perform targeted search and flag/purge in a loop to bypass Yahoo's page/search limits
            try:
                if job_type == "sender":
                    search_query = target
                    if "<" in target and ">" in target:
                        search_query = target.split("<")[1].split(">")[0].strip()
                    imap_query_args = [None, f'FROM "{search_query}"']
                else:
                    imap_query_args = [None, 'TEXT', f'"{target}"']
                    if segment != "all":
                        if segment == "2007-2012":
                            imap_query_args.extend(['SINCE', '01-Jan-2007', 'BEFORE', '01-Jan-2013'])
                        elif segment == "2013-2017":
                            imap_query_args.extend(['SINCE', '01-Jan-2013', 'BEFORE', '01-Jan-2018'])
                        elif segment == "2018-2022":
                            imap_query_args.extend(['SINCE', '01-Jan-2018', 'BEFORE', '01-Jan-2023'])
                        elif segment == "2023-2027":
                            imap_query_args.extend(['SINCE', '01-Jan-2023', 'BEFORE', '01-Jan-2028'])
                
                total_purged_for_job = 0
                loop_safety = 0
                
                while loop_safety < 100:  # Avoid infinite loops
                    sync_status.log(f"[Worker {worker_id}] Searching server for query args: {imap_query_args[1:]} (Pass {loop_safety+1})...")
                    search_result = await asyncio.to_thread(
                        mail.uid, "search", *imap_query_args
                    )
                    status, data = search_result
                    if status != "OK":
                        raise Exception(f"IMAP search failed: {data}")
                    
                    uids = data[0].split()
                    if not uids:
                        break  # No more matching emails
                        
                    uids_list = [int(uid) for uid in uids]
                    total_in_batch = len(uids_list)
                    sync_status.log(f"[Worker {worker_id}] Found {total_in_batch:,} emails matching query in this batch.")
                    
                    # Batch processing with dynamic chunk length check (< 2000 chars or 500 items)
                    batch = []
                    batch_char_count = 0
                    
                    for uid in uids_list:
                        uid_str = str(uid)
                        
                        if len(batch) >= 500 or (batch_char_count + len(uid_str) + 1) > 2000:
                            await process_flagging_batch(mail, batch)
                            batch = []
                            batch_char_count = 0
                        
                        batch.append(uid_str)
                        batch_char_count += len(uid_str) + 1
                    
                    if batch:
                        await process_flagging_batch(mail, batch)
                    
                    # Expunge immediately so they are removed from the next search iteration
                    sync_status.log(f"[Worker {worker_id}] Expunging deleted messages...")
                    await asyncio.to_thread(mail.expunge)
                    
                    total_purged_for_job += total_in_batch
                    loop_safety += 1
                
                sync_status.purging_senders[job_key] = "Done"
                sync_status.log(f"[Worker {worker_id}] Successfully finished job {job_key} ({total_purged_for_job} total emails purged).")
                
            except (imaplib.IMAP4.abort, ConnectionError, OSError) as conn_err:
                sync_status.log(f"[Worker {worker_id}] Yahoo disconnected during purge: {conn_err}")
                mail = None # Force reconnect
                sync_status.purging_senders[job_key] = "Queued"
                await _purge_queue.put(job)
            except Exception as e:
                sync_status.log(f"[Worker {worker_id}] [ERROR] Failed to purge {job_key}: {e}")
                sync_status.purging_senders[job_key] = "Error"
            finally:
                if job_key in sync_status.purge_queue:
                    sync_status.purge_queue.remove(job_key)
                _purge_queue.task_done()
                
    finally:
        if mail:
            try:
                await asyncio.to_thread(mail.logout)
            except Exception:
                pass
                
        # If queue is fully processed, set running state to false
        global _purge_workers_running
        if len(sync_status.purge_queue) == 0:
            _purge_workers_running = False
            sync_status.is_running = False
            sync_status.status = "Completed"
            sync_status.log("Bulk purging queue finished.")

async def start_empty_trash():
    # Deprecated / Staging folder no longer used in direct Flag & Purge.
    sync_status.log("Empty trash is deprecated. Direct purging flags messages as Deleted directly in the Inbox.")
    return

