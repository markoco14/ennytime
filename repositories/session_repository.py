"""CRUD functions for sessions table"""
from sqlalchemy.orm import Session
from core.memory_db import SESSIONS
from models.user_session_model import DBUserSession
import schemas

def get_session_by_session_id(db: Session, session_id: str):
    """ Returns a user by email"""
    db_user = db.query(DBUserSession).filter(
        DBUserSession.session_id == session_id).first()
    
    return db_user

def create_session(db: Session, session: schemas.CreateUserSession):
    """ Creates a session """
    
    db_user = DBUserSession(**session.model_dump())

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def destroy_session(db: Session, session_id: str):
    """ Deletes a session """
    db.query(DBUserSession).filter(
        DBUserSession.session_id == session_id
        ).delete()
    db.commit()

def list_sessions():
    """ Returns a list of sessions """
    return list(SESSIONS.values())
