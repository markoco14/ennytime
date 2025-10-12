from dataclasses import dataclass
from datetime import datetime
import sqlite3

from app.viewmodels.structs import ScheduleRow

@dataclass
class Commitment:
    id: int
    shift_id: int
    user_id: int
    date: datetime

    @classmethod
    def get(cls, commitment_id: int):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute("SELECT id, shift_id, user_id, date FROM schedules WHERE id = ?;", (commitment_id, )).fetchone()

            return ScheduleRow(
                id=row["id"],
                shift_id=row["shift_id"],
                user_id=row["user_id"],
                date=row["date"]
                )

    @classmethod
    def create(cls, shift_id, user_id, date, return_id: bool = False) -> int:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO schedules (shift_id, user_id, date) VALUES (?, ?, ?);", (shift_id, user_id, date,))

            if return_id:
                row_id = cursor.lastrowid

                return row_id
            
            return None
       
