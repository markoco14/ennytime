import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.db_shift import DbShift
from app.models.db_shift_type import DbShiftType


def get_shift_with_detail_for_user_by_date(db: Session, user_ids: List[int]) -> List[Tuple[DbShift, DbShiftType]]:
    """Returns a list of shifts for the given users."""
    return db.query(DbShift, DbShiftType).join(DbShiftType, DbShift.type_id == DbShiftType.id).filter(
        DbShift.user_id.in_(user_ids)).all()


def get_shift_detail_for_couple_by_date(db: Session, user_ids: List[int], selected_date: str) -> List[Tuple[DbShift, DbShiftType]]:
    """
    Returns a list of tuples (shift, shift_type) for the couple (two users sharing calendars) on the selected date.
    """
    return db.query(DbShift, DbShiftType
                    ).join(DbShiftType, DbShift.type_id == DbShiftType.id
                    ).filter(DbShift.user_id.in_(user_ids)
                    ).filter(DbShift.date == selected_date
                    ).order_by(DbShift.user_id).all()


def get_month_shift_info_for_users(
    db: Session,
    user_ids: List[int],
    start_of_month: datetime,
    end_of_month: datetime
    ) -> List[Tuple[DbShift, DbShiftType]]:
    """
    Returns a list of tuples (shift, shift_type) for the given users within the given month.
    """
    return db.query(DbShift, DbShiftType
                    ).join(DbShiftType, DbShift.type_id == DbShiftType.id
                    ).filter(DbShift.user_id.in_(user_ids)
                    ).filter(DbShift.date >= start_of_month
                    ).filter(DbShift.date <= end_of_month
                    ).order_by(DbShift.user_id
                    ).order_by(DbShift.date
                    ).all()