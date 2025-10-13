from dataclasses import dataclass

@dataclass
class SessionCreate:
    token: str
    user_id: int
    expires_at: int