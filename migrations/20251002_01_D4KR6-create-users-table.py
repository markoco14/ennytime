"""
Create users table
"""

from yoyo import step

__depends__ = {}

steps = [
    step("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_superuser INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            is_verified INTEGER DEFAULT 0,
            verified_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT,
            birthday TEXT,
            username TEXT UNIQUE
            );
        """,
        "DROP TABLE IF EXISTS users;")
]
