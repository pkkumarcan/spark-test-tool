# Mail Agent Subsystem Function Registry — docs/MAIL_AGENT.md

This document outlines the API endpoints, input/output structures, and database interactions of the local email cleanup and management subsystem. All routes are prefixed by `/api/mail`.

---

## 1. Synchronization and Folders

### start-sync (`POST /api/mail/sync/start`)
Starts the asynchronous task to download and index email headers from the IMAP server.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "folder": { "type": "string", "default": "INBOX" },
      "segment": { "type": "string", "default": "all" }
    }
  }
  ```
- **JSON Output Sample:**
  ```json
  { "status": "started" }
  ```

### get-folders (`GET /api/mail/folders`)
Retrieves the list of available folders from the IMAP account.
- **JSON Output Sample:**
  ```json
  {
    "folders": ["INBOX", "Sent", "Trash", "Spam", "Archive"]
  }
  ```

### stop-sync (`POST /api/mail/sync/stop`)
Halts any active background synchronization task.
- **JSON Output Sample:**
  ```json
  { "status": "stopped" }
  ```

### get-stats (`GET /api/mail/stats`)
Retrieves live processing statistics, sync status, speed metrics, and database size.
- **JSON Output Sample:**
  ```json
  {
    "is_running": false,
    "total_emails": 1500,
    "synced_emails": 1500,
    "current_speed_ups": 0.0,
    "status": "idle",
    "error_message": null,
    "db_size_mb": 1.25,
    "logs": ["Initialized..."],
    "purge_queue": [],
    "purging_senders": []
  }
  ```

---

## 2. Emails & Cleanup Queries

### get-emails (`GET /api/mail/emails`)
Fetches paginated and searchable email records from the local SQLite store.
- **Query Parameters:**
  - `page` (Integer, default: `1`)
  - `limit` (Integer, default: `50`, maximum: `100`)
  - `search` (String, optional; filters by sender or subject)
- **JSON Output Sample:**
  ```json
  {
    "emails": [
      {
        "imap_uid": 12,
        "sender": "promo@store.com",
        "subject": "50% off all items!",
        "date": "Mon, 15 Jun 2026 12:00:00 -0400",
        "category": "Marketing",
        "status": "Pending"
      }
    ],
    "total_count": 1,
    "page": 1,
    "limit": 50
  }
  ```

### cleanup (`POST /api/mail/cleanup`)
Launches the asynchronous automatic staging of old/junk emails to be purged.
- **Query Parameters:**
  - `fast` (Boolean, default: `true`)
- **JSON Output Sample:**
  ```json
  { "status": "cleanup_started" }
  ```

### cleanup-preview (`GET /api/mail/cleanup/preview`)
Calculates a preview of emails matching cleanup filters (e.g., Marketing/Social over 30 days old, Newsletters over 14 days old).
- **JSON Output Sample:**
  ```json
  {
    "total_count": 254,
    "breakdown": {
      "Marketing": 150,
      "Social": 74,
      "Newsletter": 30
    },
    "sample": [
      {
        "imap_uid": 1054,
        "sender": "newsletter@tech.com",
        "subject": "Weekly Tech Update",
        "date": "Mon, 01 Jun 2026 09:00:00 -0400",
        "category": "Newsletter",
        "age_days": 15
      }
    ]
  }
  ```

### get-senders (`GET /api/mail/senders`)
Lists the top 15 senders of pending (unprocessed) emails along with counts.
- **JSON Output Sample:**
  ```json
  {
    "senders": [
      {
        "sender": "news@updates.com",
        "email_count": 48
      }
    ]
  }
  ```

---

## 3. Purging and Staging

### stage-sender (`POST /api/mail/stage-sender`)
Stages all emails from a specific sender for deletion.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "sender": { "type": "string" }
    },
    "required": ["sender"]
  }
  ```

### stage-senders (`POST /api/mail/stage-senders`)
Stages all emails from a list of senders for deletion.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "senders": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["senders"]
  }
  ```

### empty-trash (`POST /api/mail/empty-trash`)
Triggers the physical deletion of all staged emails from the remote IMAP folder.
- **JSON Output Sample:**
  ```json
  { "status": "empty_trash_started" }
  ```

### deep-purge (`POST /api/mail/deep-purge`)
Performs a deep purge (stages and queue-deletes) for a single sender.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "sender": { "type": "string" }
    },
    "required": ["sender"]
  }
  ```

### keyword-purge (`POST /api/mail/keyword-purge`)
Stages emails matching a specific keyword for deletion.
- **JSON Input Schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "keyword": { "type": "string" },
      "segment": { "type": "string", "default": "all" }
    },
    "required": ["keyword"]
  }
  ```

### keyword-search (`GET /api/mail/keyword-search`)
Retrieves counts of emails containing the keyword segment.
- **Query Parameters:**
  - `keyword` (String, required)
- **JSON Output Sample:**
  ```json
  {
    "counts": {
      "total": 45,
      "breakdown": {
        "INBOX": 35,
        "Archive": 10
      }
    }
  }
  ```
