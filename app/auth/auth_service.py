""" Auth service functions """
from datetime import datetime, timedelta
import secrets
from typing import Dict
import logging

from sqlalchemy.orm import Session
from fastapi import Depends, Request

from passlib.context import CryptContext
from app.core.database import get_db
from app.repositories import session_repository

from app.repositories import user_repository

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


def is_session_expired(expires_at: datetime):
    if expires_at < datetime.now():
        return True
    return False


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


def user_dependency(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session-id")
    if not session_id:
        return None

    session_data = session_repository.get_session_by_session_id(
        db=db, session_id=session_id)
    if not session_data:
        return None

    if is_session_expired(session_data.expires_at):
        try:
            db.delete(session_data)
            db.commit()
            logging.info("Expired session deleted: %s", session_id)
        except Exception as error:
            db.rollback()
            logging.error(
                "Failed to delete expired session: %s, error: %s", session_id, error)
        return None

    db_user = user_repository.get_user_by_id(
        db=db, user_id=session_data.user_id)
    if not db_user:
        try:
            db.delete(session_data)
            db.commit()
            logging.info("Orphaned session deleted: %s", session_id)
        except Exception as error:
            db.rollback()
            logging.error(
                "Failed to delete orphaned session: %s, error: %s", session_id, error)
        return None

    return db_user
