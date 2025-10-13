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
    def get_by_token(cls, token: str):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute("SELECT id, token, user_id, expires_at, created_at FROM sessions WHERE token = ?;", (token, )).fetchone()

            return Session(
                id=row["id"],
                token=row["token"],
                user_id=row["user_id"],
                expires_at=row["expires_at"],
                created_at=row["created_at"]
            )

    @classmethod
    def create(cls, data: SessionCreate):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", (data.token, data.user_id, data.expires_at))

    def delete(self):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_key=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE id = ?", (self.id, ))
