"""CRUD functions for sessions table"""
from sqlalchemy.orm import Session

from models.user_session_model import DBUserSession
from app import schemas

def get_session_by_session_id(db: Session, session_id: str):
    """ Returns a user by email"""
    db_user_session = db.query(DBUserSession).filter(
        DBUserSession.session_id == session_id).first()
    
    return db_user_session

def create_session(db: Session, session: schemas.CreateUserSession):
    """ Creates a session """
    
    db_user_session = DBUserSession(**session.model_dump())

    db.add(db_user_session)
    db.commit()
    db.refresh(db_user_session)

    return db_user_session

def destroy_session(db: Session, session_id: str):
    """ Deletes a session """
    db.query(DBUserSession).filter(
        DBUserSession.session_id == session_id
        ).delete()
    db.commit()

def list_sessions(db: Session):
    """ Returns a list of sessions """
    db_user_sessions = db.query(DBUserSession).all()
    return db_user_sessions

