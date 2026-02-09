from dataclasses import dataclass
import sqlite3
from typing import Optional


@dataclass
class Shift:
    id: Optional[int] = None
    long_name: Optional[str] = None
    short_name: Optional[str] = None
    user_id: Optional[int] = None

    ALLOWED_COLUMNS = {"id", "long_name", "short_name", "user_id"}

    @classmethod
    def list_user_shifts(cls, user_id: int, columns: list[str]):
        if not columns:
            columns = cls.ALLOWED_COLUMNS
        else:
            invalid = set(columns) - cls.ALLOWED_COLUMNS
            if invalid:
                raise ValueError(f"Invalid columns requested: {invalid}")
            
        columns = ", ".join(columns).rstrip(", ")
        
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.row_factory = sqlite3.Row

            cursor = conn.cursor()
            cursor.execute(f"SELECT {columns} FROM shifts WHERE user_id = ?", (user_id, ))
            
            shifts_rows = [Shift(**row) for row in cursor.fetchall()]

        return shifts_rows
    
    @classmethod
    def get(cls, shift_id: int, columns: list[str]):
        if not columns:
            columns = cls.ALLOWED_COLUMNS
        else:
            invalid = set(columns) - cls.ALLOWED_COLUMNS
            if invalid:
                raise ValueError(f"Invalid columns requested: {invalid}")
            
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(f"SELECT {columns} FROM shifts WHERE id = ?;", (shift_id, ))
            row = cursor.fetchone()
            shift = Shift(
                id=row["id"],
                long_name=row["long_name"],
                short_name=row["short_name"],
                user_id=row["user_id"]
            )
            return shift
    
    @classmethod
    def create(cls, long_name: str, short_name: str, user_id: int):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO shifts (long_name, short_name, user_id) VALUES (?, ?, ?);", (long_name, short_name, user_id))
            row_id = cursor.lastrowid

        return row_id
    
    def update(self, long_name: str, short_name: str):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("UPDATE shifts SET long_name = ?, short_name = ? WHERE id = ?;", (long_name, short_name, self.id))
    
    def delete(self):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM shifts WHERE id = ?;", (self.id, ))
            row_id = cursor.lastrowid

        return row_id