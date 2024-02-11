"""Schemas for the application"""

from datetime import datetime
from pydantic import BaseModel


class ScheduleDay(BaseModel):
    """Schedule day"""
    date: int
    type: str


class Session(BaseModel):
    """Session"""
    session_id: str
    user_id: int
    expires_at: datetime


class User(BaseModel):
    """User"""
    id: int
    email: str
    password: str
