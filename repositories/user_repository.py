"""CRUD functions for users table"""
from sqlalchemy.orm import Session

from core.memory_db import USERS
from models.user_model import DBUser
import schemas



def get_user_by_email(db: Session, email: str):
    """ Returns a user by email"""
    db_user = db.query(DBUser).filter(
        DBUser.email == email).first()
    
    return db_user


def create_user(db: Session, user: schemas.CreateUserHashed):
    """ Creates a user """
    
    db_user = DBUser(**user.model_dump())

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def list_users():
    """ Returns a list of users """
    return list(USERS.values())


def patch_user(current_user: schemas.User, display_name: str = None):
    """ Updates a user """
    if display_name is not None:
        current_user.display_name = display_name

    USERS.update({current_user.email: current_user})



