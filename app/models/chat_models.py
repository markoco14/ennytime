
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, String, JSON
from app.core.database import Base

class DBChatRoom(Base):
    """DB Model for chat rooms"""
    __tablename__ = 'etime_chat_rooms'

    id = Column(Integer, primary_key=True)
    room_id = Column(
        String(length=255),
        nullable=False,
        index=True,
    )
    chat_users = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        onupdate=datetime.utcnow
    )
