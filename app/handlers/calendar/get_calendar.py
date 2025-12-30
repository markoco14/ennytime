
import datetime
import sqlite3
from types import SimpleNamespace
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.responses import Response, RedirectResponse
from app.core.config import get_settings
from app.core.template_utils import templates
from app.models.commitment import Commitment
from app.models.shift import Shift
from app.models.user import User
from app.services import calendar_service
from app.viewmodels.pages import CalendarMonthPage
from app.viewmodels.structs import UserRow

settings = get_settings()

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
    # because neeed to match with shifts in edit view, use shift.id as the key
    commitments = {}
    for commitment in db_commitments:
        date_key = commitment.date.strftime("%Y-%m-%d")
        shift_id = commitment.shift_id
        commitments.setdefault(date_key, {})[shift_id] = commitment
    
    bae_shifts_dict = {}
    bae_commitments = {}
    if bae_user:
        bae_db_shifts = Shift.list_user_shifts(user_id=bae_user.id)
        bae_db_commitments = Commitment.list_month_for_user(start_of_month=start_of_month, end_of_month=end_of_month, user_id=bae_user.id)

        # repackage bae shifts as dict with shift ids as keys to access with .get()
        for shift in bae_db_shifts:
            bae_shifts_dict[shift.id] = shift

        # repackage bae schedule as dict with dates as keys to access with .get()
        for commitment in bae_db_commitments:
            date_key = commitment.date.strftime("%Y-%m-%d")
            shift_id = commitment.id
            bae_commitments.setdefault(date_key, {})[shift_id] = commitment

    referer = request.headers.get('referer')
    referer_date = None
    if referer:
        try:
            referer_date = referer.split("/calendar/")[1]
        except:
            pass

    view_transition_day = None
    if referer_date:
        if (len(referer_date.split("/")) == 3 or len(referer_date.split("/")) == 4):
            view_transition_day = int(referer.split('/calendar/')[1].split("/")[2])

    # for development
    # day = 25
    # year = 2026
    # month = 1
    # day = 1
    # print('YEAR', year)
    # print('MONTH', month)
    # print('DAY', day)
    # holiday = None
    # iso_date = f"{year}-0{month}-0{day}"
    # print(iso_date)
    # end for development

    holiday_tz_date_today = datetime.datetime.now(tz=ZoneInfo('Asia/Taipei'))
    iso_date = holiday_tz_date_today.date().isoformat()

    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM holiday WHERE iso_date = ?;", (iso_date, ))
        holiday_row = cursor.fetchone()
    
    holiday = SimpleNamespace(**dict(holiday_row)) if holiday_row else None

    message_row = None
    if holiday:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM holiday_message WHERE holiday_id = ? AND recipient_id = ?;", (holiday.holiday_id, current_user.id ))
            message_row = cursor.fetchone()

    custom_holiday_message = SimpleNamespace(**dict(message_row)) if message_row else None

    context = CalendarMonthPage(
        current_user=current_user,
        bae_user=None if not bae_user else bae_user,
        days_of_week=calendar_service.DAYS_OF_WEEK,
        current_month=current_month_object,
        prev_month_object=prev_month_object,
        next_month_object=next_month_object,
        month_calendar=month_calendar_dict,
        shifts=shifts_dict,
        commitments=commitments,
        bae_shifts=bae_shifts_dict if bae_shifts_dict else {},
        bae_commitments=bae_commitments if bae_commitments else {},
        view_transition_day=view_transition_day,
        birthday_ids=settings.BIRTHDAY_IDS,
        holiday=holiday,
        custom_holiday_message=custom_holiday_message
    )

    response = templates.TemplateResponse(
        request=request,
        name="calendar/index.html",
        context=context,
    )

    return response