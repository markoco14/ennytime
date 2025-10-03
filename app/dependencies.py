"""Application dependencies"""
import sqlite3
import logging

from fastapi import Request


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

def requires_user(request: Request):
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
        
        cursor.execute("SELECT id, display_name, is_admin, birthday, username FROM users WHERE id = ?", (session[0],))
        user = cursor.fetchone()

    return user

