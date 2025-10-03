"""
Create user signins table
"""

from yoyo import step

__depends__ = {'20251003_01_rQ3lH-create-sessions-table'}

steps = [
    step("""CREATE TABLE IF NOT EXISTS user_signins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            status TEXT NOT NULL CHECK(status IN ('SUCCESS','FAILED')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );""",
        "DROP TABLE IF EXISTS user_signins;")
]
