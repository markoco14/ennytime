"""Application dependencies"""
import sqlite3
import logging

from fastapi import Request

from app.structs.structs import UserRow


def requires_guest(request: Request):
    """Checks for a session and returns a guest user"""
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

def requires_user(request: Request) -> UserRow:
    """Checks for a session and returns an authenticated user"""
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
        user = UserRow(*cursor.fetchone())

    return user


def requires_shift_owner(request: Request, shift_type_id: int):
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
        
        cursor.execute("SELECT id, display_name, is_admin, birthday, username FROM users WHERE id = ?", (session[0],))
        user = cursor.fetchone()

        cursor.execute("SELECT user_id FROM shifts WHERE id = ?", (shift_type_id, ))
        shift = cursor.fetchone()

    if user[0] != shift[0]:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (session_id, ))
        return None

    return user


def requires_schedule_owner(request: Request, schedule_id: int) -> UserRow:
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
        
        cursor.execute("SELECT id, display_name, is_admin, birthday, username FROM users WHERE id = ?", (session[0],))
        user = UserRow(*cursor.fetchone())

        cursor.execute("SELECT user_id FROM schedules WHERE id = ?", (schedule_id, ))
        schedule = cursor.fetchone()

    if user[0] != schedule[0]:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (session_id, ))
        return None

    return user


def requires_profile_owner(request: Request, user_id: int) -> UserRow:
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
        user = UserRow(*cursor.fetchone())

    if user[0] != user_id:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (session_id, ))
        return None

    return user
