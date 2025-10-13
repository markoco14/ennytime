from dataclasses import dataclass
from datetime import datetime
import sqlite3

from app.viewmodels.session import SessionCreate
@dataclass
class Session:
    id: int
    token: str
    user_id: int
    expires_at: int
    created_at: datetime

    @classmethod
    def create(cls, data: SessionCreate):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", (data.token, data.user_id, data.expires_at))