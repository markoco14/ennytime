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
    def list_month_for_user(cls, start_of_month: datetime, end_of_month: datetime, user_id: int):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""SELECT id, shift_id, user_id, date
                            FROM schedules 
                            WHERE DATE(date) BETWEEN DATE(?) and DATE(?) AND user_id = ?;
                            """,
                           (start_of_month, end_of_month, user_id))
            rows = [Commitment(
                id=row["id"],
                shift_id=row["shift_id"],
                user_id=row["user_id"],
                date=datetime.strptime(row["date"], "%Y-%m-%d %H:%M:%S")
            ) for row in cursor.fetchall()]

        return rows
    
    @classmethod
    def get(cls, commitment_id: int):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute("SELECT id, shift_id, user_id, date FROM schedules WHERE id = ?;", (commitment_id, )).fetchone()

            return Commitment(
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
        

    def delete(self):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM schedules WHERE id = ?;", (self.id, ))
       
