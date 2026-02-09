"""Application dependencies"""
import sqlite3
import logging

from fastapi import Request

from app.models.session import Session
from app.models.shift import Shift
from app.models.user import User


def requires_guest(request: Request) -> User:
    """Checks for a session and returns a guest user"""
    session_token = request.cookies.get("session-id")

    if not session_token:
        logging.info("User dependency no session token found")
        return None
    
    session = Session.get_dependency(token=session_token, columns=["id", "user_id"])

    if not session:
        logging.info("User dependency no session found")
        return None
        
    user = User.get_current_user(user_id=session.user_id)

    return user

def requires_user(request: Request) -> User:
    """Checks for a session and returns an authenticated user"""
    session_token = request.cookies.get("session-id")

    if not session_token:
        logging.info("User dependency no session token found")
        return None
    
    session = Session.get_dependency(token=session_token, columns=["id", "user_id"])

    if not session:
        logging.info("User dependency no session found")
        return None
        
    user = User.get_current_user(user_id=session.user_id)

    return user


def requires_shift_owner(request: Request, shift_type_id: int) -> User:
    """Checks for a session and checks the user owns the resource before returns an authenticated user"""
    session_token = request.cookies.get("session-id")

    if not session_token:
        logging.info("User dependency no session token found")
        return None
    
    session = Session.get_dependency(token=session_token, columns=["id", "user_id"])

    if not session:
        logging.info("User dependency no session found")
        return None
    
    user = User.get_current_user(user_id=session.user_id)

    if not user:
        return None
    
    shift = Shift.get(shift_id=shift_type_id, columns=["user_id"])

    if not shift or user.id != shift.user_id:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session.id, ))
        return None

    return user


def requires_schedule_owner(request: Request, schedule_id: int) -> User:
    """Checks for a session and checks the user owns the resource before returns an authenticated user"""
    session_id = request.cookies.get("session-id")

    if not session_id:
        logging.info("User dependency no session id found")
        return None
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (session_id, ))
        session = cursor.fetchone()
        
        cursor.execute("SELECT id, display_name, is_admin, birthday, username, email FROM users WHERE id = ?", (session[0],))
        user = User(*cursor.fetchone())

        cursor.execute("SELECT user_id FROM schedules WHERE id = ?", (schedule_id, ))
        schedule = cursor.fetchone()

    if user[0] != schedule[0]:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (session_id, ))
        return None

    return user


def requires_profile_owner(request: Request, user_id: int) -> User:
    session_id = request.cookies.get("session-id")
    if not session_id:
        logging.info("User dependency no session id found")
        return None
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (session_id, ))
        session = cursor.fetchone()
        
        cursor.execute("SELECT id, display_name, is_admin, birthday, username, email FROM users WHERE id = ?", (session[0],))
        user = User(*cursor.fetchone())

    if user[0] != user_id:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (session_id, ))
        return None

    return user

def requires_admin(request: Request):
    session_id = request.cookies.get("session-id")
    if not session_id:
        logging.info("User dependency no session id found")
        return None
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (session_id, ))
        session = cursor.fetchone()
        
        cursor.execute("SELECT id, display_name, is_admin, birthday, username, email FROM users WHERE id = ?", (session[0],))
        user = User(*cursor.fetchone())

    if not user.is_admin:
        return None

    return user

