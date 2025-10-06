"""
Create shares table
"""

from yoyo import step

__depends__ = {'20251003_02_8821X-create-user-signins-table'}

steps = [
    step("""
        CREATE TABLE IF NOT EXISTS shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER UNIQUE NOT NULL,
            receiver_id INTEGER UNIQUE NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT,
            FOREIGN KEY(sender_id) references users(id) ON DELETE CASCADE,
            FOREIGN KEY(receiver_id) references users(id) ON DELETE CASCADE
        );
         
    """,
    "DROP TABLE IF EXISTS shares;"),
    step("CREATE INDEX IF NOT EXISTS idx_shares_sender_id ON shares (sender_id);",
    "DROP INDEX IF EXISTS idx_shares_sender_id;"),
    step("CREATE INDEX IF NOT EXISTS idx_shares_receiver_id ON shares (receiver_id);",
    "DROP INDEX IF EXISTS idx_shares_receiver_id;")
]
