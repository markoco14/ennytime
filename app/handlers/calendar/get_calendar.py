
import datetime
import sqlite3
from typing import Optional
from fastapi import Request
from fastapi.responses import Response, RedirectResponse
from app.core.template_utils import templates, block_templates
from app.services import calendar_service
from app.structs.pages import CalendarMonthPage
from app.structs.structs import ScheduleRow, ShiftRow, UserRow


def get_calendar(
    request: Request,
    year: int,
    month: int,
    current_user: UserRow,
    day: Optional[int] = None
    ):
    """Returns calendar month view."""
    if not current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/"})
        else:
            return RedirectResponse(status_code=303, url=f"/")

    current_month_object = datetime.date(year=year, month=month, day=1)

    # for calendar controls
    prev_month_object = datetime.date(year=year if month != 1 else year - 1, month=month - 1 if month != 1 else 12, day=1)
    next_month_object = datetime.date(year=year if month != 12 else year + 1, month=month + 1 if month != 12 else 1, day=1)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT users.id, users.display_name, users.is_admin, users.birthday, users.email, users.email FROM users JOIN shares ON shares.sender_id = ? WHERE users.id = shares.receiver_id;", (current_user.id, ))
        bae_user = UserRow(*cursor.fetchone())
    
    month_calendar = calendar_service.get_month_calendar(
        year=current_month_object.year, 
        month=current_month_object.month
        )
    
    month_calendar_dict = {}
    for date in month_calendar:
        month_calendar_dict[date] = date
    
    # get the start and end of the month for query filters
    start_of_month = calendar_service.get_start_of_month(year=current_month_object.year, month=current_month_object.month)
    end_of_month = calendar_service.get_end_of_month(year=current_month_object.year, month=current_month_object.month)

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()

        # get current user shift types
        cursor.execute("SELECT id, long_name, short_name FROM shifts WHERE user_id = ?;", (current_user.id,))
        shift_rows = [ShiftRow(*row) for row in cursor.fetchall()]

        # get current user bae_schedules for month
        cursor.execute("SELECT id, shift_id, user_id, date FROM schedules WHERE DATE(date) BETWEEN DATE(?) and DATE(?) AND user_id = ?;", (start_of_month, end_of_month, current_user[0]))
        schedule_rows = [ScheduleRow(*row) for row in cursor.fetchall()]

        # get bae user shift types
        cursor.execute("SELECT id, long_name, short_name FROM shifts WHERE user_id = ?;", (bae_user.id,))
        bae_shifts = [ShiftRow(*row) for row in cursor.fetchall()]

        # get bae user schedules for month
        cursor.execute("SELECT id, shift_id, user_id, date FROM schedules WHERE DATE(date) BETWEEN DATE(?) and DATE(?) AND user_id = ?;", (start_of_month, end_of_month, bae_user.id))
        bae_schedules = [ScheduleRow(*row) for row in cursor.fetchall()]

    # repackage current user shifts as dict with shift ids as keys to access with .get()
    shifts_dict = {}
    for shift in shift_rows:
        shifts_dict[shift.id] = shift
        
    # repackage current user schedule as dict with dates as keys to access with .get()
    schedules = {}
    for schedule in schedule_rows:
        date_key = schedule[3].split()[0]
        shift_id = schedule[1]
        schedules.setdefault(date_key, {})[shift_id] = schedule

    # repackage bae shifts as dict with shift ids as keys to access with .get()
    bae_shifts_dict = {}
    for shift in bae_shifts:
        bae_shifts_dict[shift.id] = shift

    # repackage bae schedule as dict with dates as keys to access with .get()
    bae_commitments = {}
    for schedule in bae_schedules:
        date_key = schedule[3].split()[0]
        shift_id = schedule[1]
        bae_commitments.setdefault(date_key, {})[shift_id] = schedule

    context = CalendarMonthPage(
        current_user=current_user,
        days_of_week=calendar_service.DAYS_OF_WEEK,
        current_month=current_month_object,
        prev_month_object=prev_month_object,
        next_month_object=next_month_object,
        month_calendar=month_calendar_dict,
        shifts=shifts_dict,
        schedules=schedules,
        bae_shifts=bae_shifts_dict,
        bae_commitments=bae_commitments
    )

    response = templates.TemplateResponse(
        request=request,
        name="calendar/v2/index.html",
        context=context,
    )

    return response