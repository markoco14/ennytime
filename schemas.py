"""Schemas for the application"""

from datetime import datetime
from pydantic import BaseModel


class ScheduleDay(BaseModel):
    """Schedule day"""
    date: int
    type: str


class ShiftType(BaseModel):
    """Shift type"""
    id: int
    type: str
    user_id: int

class Shift(BaseModel):
    id: int
    type_id: int
    user_id: int
    date: datetime

class Session(BaseModel):
    """Session"""
    id: int
    session_id: str
    user_id: int
    expires_at: datetime


class User(BaseModel):
    """User"""
    id: int
    email: str
    password: str
