"""
Functions for retrieving data from any table in the database
"""
from sqlalchemy import text
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


def get_user_shifts(db: Session, user_id: int):
    """ Get shift by date """
    return db.query(DbShift).filter(DbShift.user_id == user_id).order_by(DbShift.date).all()


def get_user_shifts_details(db: Session, user_id: int):
    """ Get shifts by User with shift type details """
    query = text("""
        SELECT etime_shifts.*, etime_shift_types.type as type_name
        FROM etime_shifts
        JOIN etime_shift_types ON etime_shifts.type_id = etime_shift_types.id
        WHERE etime_shifts.user_id = :user_id
        ORDER BY etime_shifts.date
    """)
    result = db.execute(query, {"user_id": user_id})
    return result.fetchall()


def delete_user_shift(db: Session, shift_id: int):
    """ Delete shift """
    db.query(DbShift).filter(DbShift.id == shift_id).delete()
    db.commit()
