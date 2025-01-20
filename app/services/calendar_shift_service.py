import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.db_shift import DbShift
from app.models.db_shift_type import DbShiftType
from app.models.user_model import DBUser


def sort_shifts_by_user(all_shifts: List[Tuple[DbShift, DbShiftType]], month_calendar_dict, current_user: DBUser) -> dict:
    """Takes a list of shifts and sorts them into a dictionary by date and user"""
    for shift, shift_type in all_shifts:
        shift_date = str(shift.date.date())
        shift.long_name = shift_type.long_name
        shift.short_name = shift_type.short_name
        if month_calendar_dict.get(shift_date):
            # find current user shifts
            if shift.user_id == current_user.id:
                month_calendar_dict[shift_date]['shifts'].append(
                    shift.__dict__)
            # find bae user shifts
            else:
                month_calendar_dict[shift_date]['bae_shifts'].append(
                    shift.__dict__)

    return month_calendar_dict