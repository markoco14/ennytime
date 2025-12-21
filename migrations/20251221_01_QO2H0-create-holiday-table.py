"""
Create holiday table
"""

from yoyo import step

__depends__ = {'20251006_01_jMpLp-create-shares-table'}

steps = [
    step("""CREATE TABLE holiday (
                holiday_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                iso_date TEXT,
                template_name TEXT
            );
         """,
         "DROP TABLE IF EXISTS holiday;")
]
