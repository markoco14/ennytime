from dataclasses import dataclass
from datetime import datetime
import sqlite3

@dataclass
class User:
    id: int
    display_name: str
    first_name: str
    last_name: str
    email: str
    hashed_password: str
    birthday: str
    username: str
    is_superuser: bool
    is_admin: bool
    is_active: bool
    is_verified: bool
    verified_at: datetime
    created_at: datetime
    updated_at: datetime

    @classmethod
    def get(cls, user_id):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            cursor = conn.cursor()
            row = cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id, )).fetchone()
            user = User(*row)
            return user


