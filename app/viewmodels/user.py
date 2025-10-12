from dataclasses import dataclass
from datetime import datetime
import sqlite3

@dataclass
class CurrentUser:
    id: int
    display_name: str
    email: str
    birthday: datetime
    username: str
    is_admin: bool

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        return cls(
            id=row["id"],
            display_name=row["display_name"],
            email=row["email"],
            birthday=row["birthday"],
            username=row["username"],
            is_admin=row["is_admin"]
        )