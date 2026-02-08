from dataclasses import dataclass
from datetime import datetime
import sqlite3
from typing import Optional

from fastapi.datastructures import FormData

from app.viewmodels.user import CurrentUser

@dataclass
class User:
    id: int
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    hashed_password: Optional[str] = None
    birthday: Optional[str] = None
    username: Optional[str] = None
    is_superuser: Optional[bool] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def get_current_user(cls, user_id):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute("SELECT id, display_name, email, birthday, username, is_admin FROM users WHERE id = ?;", (user_id, )).fetchone()

            if not row:
                return None

            user = User(**row)

            return user

    @classmethod
    def get(cls, user_id):
        """Returns User instance."""
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id, )).fetchone()

            if not row:
                return None

            user = User(**row)

            return user
        
    @classmethod
    def username_exists(cls, username) -> bool:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute("SELECT EXISTS(SELECT 1 FROM users WHERE username = ?);", (username, )).fetchone()
            
            return bool(row[0])

    def update(self, form_data: FormData):
        if form_data.get("display_name"):
            with sqlite3.connect("db.sqlite3") as conn:
                conn.execute("PRAGMA foreign_keys=ON;")
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET display_name = ? WHERE id = ?;", (form_data.get("display_name"), self.id))
            
        if form_data.get("app_username"):
            with sqlite3.connect("db.sqlite3") as conn:
                conn.execute("PRAGMA foreign_keys=ON;")
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET username = ? WHERE id = ?;", (form_data.get("app_username"), self.id))
        
        if form_data.get("birthday"):
            with sqlite3.connect("db.sqlite3") as conn:
                conn.execute("PRAGMA foreign_keys=ON;")
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET birthday = ? WHERE id = ?;", (form_data.get("birthday"), self.id))