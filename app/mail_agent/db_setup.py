import os
import sqlite3

DB_PATH = os.getenv("MAIL_DB_PATH", "/app/output/mail_state.db")

def init_db():
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # Create emails table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            imap_uid INTEGER PRIMARY KEY,
            sender TEXT,
            subject TEXT,
            date TEXT,
            category TEXT DEFAULT 'Pending',
            status TEXT DEFAULT 'Pending'
        )
    """)
    
    # Create indexes for high-speed query
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_date ON emails(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category)")
    
    conn.commit()
    conn.close()
    print(f"SQLite Mail database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_db()
