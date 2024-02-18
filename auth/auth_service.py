""" Auth service functions """
from datetime import datetime, timedelta
import secrets
from typing import Dict

from sqlalchemy.orm import Session

from passlib.context import CryptContext
from core.memory_db import USERS
from repositories import user_repository, session_repository
from app import schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    """returns hashed password"""
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """returns True if password is correct, False if not"""
    return pwd_context.verify(plain_password, hashed_password)


def generate_session_token():
    return secrets.token_hex(16)


def generate_session_expiry():
    return datetime.now() + timedelta(days=3)

def get_session_cookie(cookies: Dict[str, str]):
    if not cookies.get("session-id"):
        return False
    
    return True

def destroy_db_session(db: Session, session_token: str):
    session_repository.destroy_session(db=db, session_id=session_token)

def is_session_expired(expiry: datetime):
    if expiry < datetime.now():
        return True
        

def get_session_data(db: Session, session_token: str):
    session_data = session_repository.get_session_by_session_id(db=db, session_id=session_token)
    return session_data

def get_current_user(db: Session, user_id: int) -> schemas.AppUser:
    db_user = user_repository.get_user_by_id(db=db, user_id=user_id)
    return db_user
    