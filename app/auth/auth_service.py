""" Auth service functions """
import re
from datetime import datetime, timedelta, timezone
import secrets
import sqlite3
import time
from typing import Dict
import logging

from sqlalchemy.orm import Session
from fastapi import Depends, Request

from passlib.context import CryptContext
from app.core.database import get_db
from app.models.user_model import DBUser
from app.models.user_session_model import DBUserSession
from app.repositories import session_repository

from app.repositories import user_repository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    """returns hashed password"""
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """returns True if password is correct, False if not"""
    return pwd_context.verify(plain_password, hashed_password)

def is_valid_email(email: str) -> bool:
        # Define the regular expression for validating an email
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

        # Use the re.match() function to check if the email matches the pattern
        return re.match(email_regex, email) is not None


def generate_session_token():
    return secrets.token_hex(16)


def generate_session_expiry():
    return datetime.now(tz=timezone.utc) + timedelta(days=3)


# currently unused function due to change to db user join db session query
def is_session_expired(expires_at: datetime):
    if expires_at < datetime.now(tz=timezone.utc):
        return True
    return False

def get_session_cookie(cookies: Dict[str, str]):
    if not cookies.get("session-id"):
        return False

    return True


def destroy_db_session(db: Session, session_token: str):
    session_repository.destroy_session(db=db, session_id=session_token)




def get_session_data(db: Session, session_token: str):
    session_data = session_repository.get_session_by_session_id(
        db=db, session_id=session_token)
    return session_data


def get_current_user(db: Session, user_id: int):
    db_user = user_repository.get_user_by_id(db=db, user_id=user_id)
    return db_user


def get_current_session_user(db: Session, cookies: Dict[str, str]):
    session_id = cookies.get("session-id")
    if not session_id:
        return None

    session_data = get_session_data(db=db, session_token=session_id)
    if not session_data:
        return None

    db_user = user_repository.get_user_by_id(
        db=db, user_id=session_data.user_id)
    if not db_user:
        return None

    return db_user

def requires_guest(request: Request):
    session_id = request.cookies.get("session-id")

    if not session_id:
        logging.info("User dependency no session id found")
        return None
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (session_id, ))
        session = cursor.fetchone()
        
        cursor.execute("SELECT id, display_name, is_admin, birthday, username FROM users WHERE id = ?", (session[0],))
        user = cursor.fetchone()

    return user

def requires_user(request: Request):
    session_id = request.cookies.get("session-id")

    if not session_id:
        logging.info("User dependency no session id found")
        return None
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (session_id, ))
        session = cursor.fetchone()
        
        cursor.execute("SELECT id, display_name, is_admin, birthday, username FROM users WHERE id = ?", (session[0],))
        user = cursor.fetchone()

    return user



def user_dependency(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session-id")

    if not session_id:
        logging.info("User dependency no session id found")
        return None
    
    query_start_time = time.perf_counter()
    db_user = db.query(DBUser
                        ).join(DBUserSession, DBUser.id == DBUserSession.user_id
                        ).filter(DBUserSession.session_id == session_id
                        ).filter(DBUserSession.expires_at > datetime.now(tz=timezone.utc)
                        ).first()
    logging.info(f"User dependency query time: {time.perf_counter() - query_start_time:.6f} seconds")

    if not db_user:
        logging.info("User dependency no user found")
        return None    

    return db_user


def update_user_password(db: Session, user_id: int, new_password: str):
    hashed_password = get_password_hash(new_password)
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    db_user.hashed_password = hashed_password
    db.commit()
