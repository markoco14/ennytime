"""
Create shifts table
"""

from yoyo import step

__depends__ = {'20251002_01_D4KR6-create-users-table'}

steps = [
    step("""
        CREATE TABLE shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_name TEXT NOT NULL,
            short_name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """,
    "DROP TABLE IF EXISTS shifts;")
]
