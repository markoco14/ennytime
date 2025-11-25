import datetime
from typing import TypedDict

from app.viewmodels.structs import ScheduleRow, ShiftRow, UserRow

class CalendarMonthPage(TypedDict):
    current_user: UserRow
    current_month: datetime.date
    prev_month_object: datetime.date
    next_month_object: datetime.date
    days_of_week: list[str]
    month_calendar: dict
    shifts: dict
    schedules: dict
    bae_shifts: dict
    bae_commitments: dict
    view_transition_day: str
    birthday_ids: list[int]

class ScheduleMonthPage(TypedDict):
    current_date: datetime.date
    current_user: UserRow
    prev_month_name: str
    next_month_name: str
    month_calendar: dict
    shifts: list[any]
    schedules: dict

class YesShiftBtn(TypedDict):
    shift: ShiftRow
    schedule: ScheduleRow
    
class NoShiftBtn(TypedDict):
    date: datetime.date
    shift: ShiftRow


class ProfilePage(TypedDict):
    current_user: UserRow
