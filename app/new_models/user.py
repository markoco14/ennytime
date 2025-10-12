from dataclasses import dataclass
from datetime import datetime
import sqlite3

from app.viewmodels.user import CurrentUser

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
    def get_current_user(cls, user_id):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute("SELECT id, display_name, email, birthday, username, is_admin FROM users WHERE id = ?;", (user_id, )).fetchone()

            if not row:
                return None

            user = CurrentUser.from_row(row=row)

            return user


