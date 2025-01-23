
from datetime import datetime

from sqlalchemy import Column, Integer, Boolean, DateTime, String, JSON, Text
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
    is_active = Column(
        Boolean,
        nullable=False,
        default=1
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


class DBChatroomUser(Base):
    """DB Model for chat users"""
    __tablename__ = 'etime_chatroom_users'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    room_id = Column(String(length=255), nullable=False, index=True)


class DBChatMessage(Base):
    """
    DB Model for chat messages
    is_read tracks whether or not the receiver has read it. In this case, there will only ever be one receiver in the couple's chat.
    """
    __tablename__ = 'etime_chat_messages'

    id = Column(Integer, primary_key=True)
    room_id = Column(
        String(length=255),
        nullable=False,
        index=True,
    )
    message = Column(Text, nullable=False)
    sender_id = Column(Integer, nullable=False, index=True)
    is_read = Column(Boolean, nullable=False, default=0)
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
    