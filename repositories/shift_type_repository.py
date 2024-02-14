"""
Functions for retrieving data from any table in the database
"""
from sqlalchemy.orm import Session
from core.memory_db import SHIFT_TYPES
from models.db_shift_type import DbShiftType
import schemas

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

def get_shift_type(shift_type_id: int):
	""" Returns a shift type for a given shift type id """
	shift_type = SHIFT_TYPES.get(shift_type_id)
	
	return shift_type

