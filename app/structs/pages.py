import datetime
from typing import TypedDict

from app.structs.structs import UserRow


class ScheduleMonthPage(TypedDict):
    current_date: datetime.date
    current_user: UserRow
    prev_month_name: str
    next_month_name: str
    month_calendar: dict
    lite_shifts: list[any]
    commitments: dict


