from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.core.database import Base

class SigninStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"

class DBUserSignin(Base):
    __tablename__ = "etime_user_signins"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("etime_users.id"), nullable=False)
    signin_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ip_address = Column(String(45), nullable=True)  # To store IPv4/IPv6 addresses
    user_agent = Column(String(255), nullable=True)  # To store browser/user-agent details
    status = Column(SQLEnum(SigninStatus), nullable=False)  # success/fail
    
    # Establish relationship with User model
    # user = relationship("User", back_populates="signins")
