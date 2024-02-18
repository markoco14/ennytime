"""CRUD functions for users table"""
from sqlalchemy.orm import Session

from app.models.user_model import DBUser
from app import schemas



def get_user_by_email(db: Session, email: str):
    """ Returns a user by email"""
    db_user = db.query(DBUser).filter(
        DBUser.email == email).first()
    
    return db_user

def get_user_by_id(db: Session, user_id: int):
    db_user = db.query(DBUser).filter(
        DBUser.id == user_id).first()
    
    return db_user



def create_user(db: Session, user: schemas.CreateUserHashed) -> schemas.AppUser:
    """ Creates a user """
    
    db_user = DBUser(**user.model_dump())

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def list_users(db: Session):
    """ Returns a list of users """
    db_users = db.query(DBUser).all()
    return db_users


def patch_user(
        db: Session,
        updated_user: DBUser,
        ):
    """ Updates a user """
    db.commit()
    db.refresh(updated_user)

    return updated_user

def list_users_by_display_name(db: Session, current_user_id: int, display_name: str):
    """ 
    Returns a list of users by display name.
    display_name: the name of the user to search for.
    current_user_id: used to exclude the current user from the search results. The current user shouldn't be able to search for or share with themselves.
    """
    
    db_users = db.query(DBUser).filter(
        DBUser.display_name.contains(display_name)).filter(DBUser.id != current_user_id).all()
    
    return db_users
