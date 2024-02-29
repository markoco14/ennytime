"""
Functions for retrieving data from any table in the database
"""
from sqlalchemy.orm import Session
from app.models.db_shift import DbShift
from app.schemas import schemas

def create_shift(db: Session, shift: schemas.CreateShift):
	""" Creates a new shift type """
	db_shift_type = DbShift(**shift.model_dump())
	
	db.add(db_shift_type)
	db.commit()
	db.refresh(db_shift_type)
	
	return db_shift_type

def get_user_shifts(db: Session, user_id: int) -> list[schemas.AppShift]:
	""" Get shift by date """
	return db.query(DbShift).filter(DbShift.user_id == user_id).order_by(DbShift.date)


def delete_user_shift(db: Session, shift_id: int):
	""" Delete shift """
	db.query(DbShift).filter(DbShift.id == shift_id).delete()
	db.commit()

