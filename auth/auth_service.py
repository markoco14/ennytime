""" Auth service functions """
from datetime import datetime, timedelta
import secrets
from typing import Dict

from passlib.context import CryptContext
from core.memory_db import SESSIONS, USERS

from schemas import Session

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

def destroy_db_session(session_token):
    SESSIONS.pop(session_token)

def is_session_expired(expiry: datetime):
    if expiry < datetime.now():
        return True
        

def get_session_data(session_token):
    session_data: Session = SESSIONS.get(session_token)
    return session_data

def get_current_user(user_id: int):
     # get users as a list (from memory db)
    db_users = list(USERS.values())

    # find the user in the list
    for user in db_users:
        if user.id == user_id:
            current_user = user

    return current_user