"""
DB model for users
"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime
from app.core.database import Base


class DBUserSession(Base):
    """
    DB model for users
    """
    __tablename__ = 'etime_user_sessions'

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True),
                        nullable=False, default=datetime.utcnow)
