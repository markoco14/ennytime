import datetime
from typing import TypedDict

from app.models.commitment import Commitment
from app.models.shift import Shift
from app.models.user import User

class CalendarMonthPage(TypedDict):
    current_user: User
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
    current_user: User
    prev_month_name: str
    next_month_name: str
    month_calendar: dict
    shifts: list[any]
    schedules: dict

class YesShiftBtn(TypedDict):
    shift: Shift
    schedule: Commitment
    
class NoShiftBtn(TypedDict):
    date: datetime.date
    shift: Shift


class ProfilePage(TypedDict):
    current_user: User
