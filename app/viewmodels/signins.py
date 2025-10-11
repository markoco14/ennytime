from dataclasses import dataclass
from datetime import datetime

@dataclass
class SigninRow:
    display_name: str
    created_at: datetime
    status: str