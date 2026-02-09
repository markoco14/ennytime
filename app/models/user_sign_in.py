from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class UserSignIn:
    id: int
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None

    display_name: Optional[str] = None