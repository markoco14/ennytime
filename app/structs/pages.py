import datetime
from typing import TypedDict

from app.structs.structs import ShiftRow, UserRow

class CalendarMonthPage(TypedDict):
    current_user: UserRow
    current_month: datetime.date
    prev_month_object: datetime.date
    next_month_object: datetime.date
    days_of_week: list[str]
    month_calendar: dict
    shifts: dict
    commitments: dict

class ScheduleMonthPage(TypedDict):
    current_date: datetime.date
    current_user: UserRow
    prev_month_name: str
    next_month_name: str
    month_calendar: dict
    lite_shifts: list[any]
    commitments: dict


class ProfilePage(TypedDict):
    current_user: UserRow
