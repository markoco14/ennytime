
import datetime
import sqlite3
from typing import Optional

from fastapi import Request
from fastapi.responses import Response, RedirectResponse

from app.core.template_utils import templates
from app.new_models.commitment import Commitment
from app.new_models.shift import Shift
from app.new_models.user import User
from app.services import calendar_service
from app.structs.pages import CalendarMonthPage
from app.viewmodels.structs import ScheduleRow, ShiftRow, UserRow


def get_calendar(
    request: Request,
    year: int,
    month: int,
    current_user: User,
    day: Optional[int] = None
    ):
    """Returns calendar month view."""
    if not current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/"})
        else:
            return RedirectResponse(status_code=303, url=f"/")
    if not day:
        day = 1
        
    current_month_object = datetime.date(year=year, month=month, day=day)

    # for calendar controls
    prev_month_object = datetime.date(year=year if month != 1 else year - 1, month=month - 1 if month != 1 else 12, day=1)
    next_month_object = datetime.date(year=year if month != 12 else year + 1, month=month + 1 if month != 12 else 1, day=1)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT users.id, users.display_name, users.is_admin, users.birthday, users.email, users.email FROM users JOIN shares ON shares.sender_id = ? WHERE users.id = shares.receiver_id;", (current_user.id, ))
        bae_row = cursor.fetchone()
        bae_user = UserRow(*bae_row) if bae_row else None
    
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

    db_shifts = Shift.list_user_shifts(user_id=current_user.id)
    db_commitments = Commitment.list_month_for_user(start_of_month=start_of_month, end_of_month=end_of_month, user_id=current_user.id)

    # repackage current user shifts as dict with shift ids as keys to access with .get()
    shifts_dict = {}
    for shift in db_shifts:
        shifts_dict[shift.id] = shift
        
    # repackage current user schedule as dict with dates as keys to access with .get()
    commitments = {}
    for commitment in db_commitments:
        date_key = commitment.date.strftime("%Y-%m-%d")
        shift_id = commitment.id
        commitments.setdefault(date_key, {})[shift_id] = commitment
    
    if bae_user:
        bae_db_shifts = Shift.list_user_shifts(user_id=bae_user.id)
        bae_db_commitments = Commitment.list_month_for_user(start_of_month=start_of_month, end_of_month=end_of_month, user_id=bae_user.id)

        # repackage bae shifts as dict with shift ids as keys to access with .get()
        bae_shifts_dict = {}
        for shift in bae_db_shifts:
            bae_shifts_dict[shift.id] = shift

        # repackage bae schedule as dict with dates as keys to access with .get()
        bae_commitments = {}
        for commitment in bae_db_commitments:
            date_key = commitment.date.strftime("%Y-%m-%d")
            shift_id = commitment.id
            bae_commitments.setdefault(date_key, {})[shift_id] = commitment

    context = CalendarMonthPage(
        current_user=current_user,
        bae_user=bae_user if bae_user else None,
        days_of_week=calendar_service.DAYS_OF_WEEK,
        current_month=current_month_object,
        prev_month_object=prev_month_object,
        next_month_object=next_month_object,
        month_calendar=month_calendar_dict,
        shifts=shifts_dict,
        commitments=commitments,
        bae_shifts=bae_shifts_dict if bae_shifts_dict else {},
        bae_commitments=bae_commitments if bae_commitments else {}
    )

    response = templates.TemplateResponse(
        request=request,
        name="calendar/v2/index.html",
        context=context,
    )

    return response