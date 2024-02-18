"""
Functions for retrieving data from any table in the database
"""
from sqlalchemy.orm import Session
from app.models.db_shift_type import DbShiftType
from app import schemas
def list_user_shift_types(db: Session, user_id: int):
    """ Returns a list of shift types for a given user """
    shift_types = db.query(
        DbShiftType
        ).filter(
            DbShiftType.user_id == user_id
        ).all()

    
    return shift_types

def create_shift_type(db: Session, shift_type: schemas.CreateShiftType):
    """ Creates a new shift type """
    db_shift_type = DbShiftType(**shift_type.model_dump())
    
    db.add(db_shift_type)
    db.commit()
    db.refresh(db_shift_type)
    
    return db_shift_type

def get_user_shift_type(db: Session, user_id: int, shift_type_id: int):
    """ Returns shift type details for a given shift type id belonging to a user """
    shift_type = db.query(
        DbShiftType
        ).filter(
            DbShiftType.id == shift_type_id,
            DbShiftType.user_id == user_id
        ).first()

    
    return shift_type

