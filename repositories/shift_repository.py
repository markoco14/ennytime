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
