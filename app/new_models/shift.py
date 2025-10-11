from dataclasses import dataclass
import sqlite3

from app.viewmodels.structs import ShiftRow

@dataclass
class Shift:
    id: int
    long_name: str
    short_name: str
    user_id: int

    @classmethod
    def get_user_shifts(cls, user_id: int):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("SELECT id, long_name, short_name FROM shifts WHERE user_id = ?", (user_id, ))
            shifts_rows = [ShiftRow(*row) for row in cursor.fetchall()]

        return shifts_rows