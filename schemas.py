"""Schemas for the application"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ShiftType(BaseModel):
    """Shift type"""
    id: int
    type: str
    user_id: int

class CreateShiftType(BaseModel):
    "Create shift type"
    type: str
    user_id: int


class Shift(BaseModel):
    """Shift data class"""
    id: int
    type_id: int
    user_id: int
    date: datetime
    type: Optional[ShiftType] = None

class AppShift(BaseModel):
    id: int
    type_id: int
    user_id: int
    date: datetime

class CreateShift(BaseModel):
    """Create shift"""
    type_id: int
    user_id: int
    date: datetime


class Session(BaseModel):
    """Session"""
    id: int
    session_id: str
    user_id: int
    expires_at: datetime

class AppUserSession(BaseModel):
    """In App User Session"""
    id: int
    session_id: str
    user_id: int
    expires_at: datetime


class CreateUserSession(BaseModel):
    """Create user session"""
    session_id: str
    user_id: int
    expires_at: datetime


class User(BaseModel):
    """User"""
    id: int
    email: str
    password: str
    display_name: Optional[str] = None


class AppUser(BaseModel):
    """User"""
    id: int
    email: str
    display_name: Optional[str] = None

class CreateUser(BaseModel):
    """Create user"""
    email: str
    password: str

class CreateUserHashed(BaseModel):
    email: str
    hashed_password: str

class Share(BaseModel):
    """Shares"""
    id: int
    owner_id: int
    guest_id: int

class CreateShare(BaseModel):
    """Create share"""
    owner_id: int
    guest_id: int
