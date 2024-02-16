"""
Functions for retrieving data from any table in the database
"""
from sqlalchemy.orm import Session
from core.memory_db import SHIFT_TYPES
from models.db_shift import DbShift
import schemas

def create_shift(db: Session, shift: schemas.CreateShift):
	""" Creates a new shift type """
	db_shift_type = DbShift(**shift.model_dump())
	
	db.add(db_shift_type)
	db.commit()
	db.refresh(db_shift_type)
	
	return db_shift_type

def get_user_shifts(db: Session, user_id: int):
	""" Get shift by date """
	return db.query(DbShift).filter(DbShift.user_id == user_id)
