"""
Create schedules table
"""

from yoyo import step

__depends__ = {'20251002_02_9zur8-create-shifts-table'}

steps = [
    step("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(shift_id) REFERENCES shifts(id),
            FOREIGN KEY(user_id) REFERENCES users(id) 
        );
    """,
    "DROP TABLE IF EXISTS schedules;")
]
