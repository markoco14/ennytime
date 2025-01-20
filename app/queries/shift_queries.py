import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.db_shift import DbShift
from app.models.db_shift_type import DbShiftType


def get_month_shift_info_for_users(
    db: Session,
    user_ids: List[int],
    start_of_month: datetime,
    end_of_month: datetime
    ) -> List[Tuple[DbShift, DbShiftType]]:
    """Returns a list of shifts for the given users within the given month"""
    return db.query(DbShift, DbShiftType
                    ).join(DbShiftType, DbShift.type_id == DbShiftType.id
                    ).filter(DbShift.user_id.in_(user_ids)
                    ).filter(DbShift.date >= start_of_month
                    ).filter(DbShift.date <= end_of_month
                    ).order_by(DbShift.user_id
                    ).order_by(DbShift.date
                    ).all()