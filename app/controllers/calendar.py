"""
Calendar related routes
"""
import sqlite3
from typing import Annotated
import datetime

from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi import Depends, Request, Response

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates, block_templates
from app.handlers.get_calendar_day import handle_get_calendar_day
from app.handlers.get_calendar_day_edit import handle_get_calendar_day_edit
from app.models.user_model import DBUser
from app.repositories import shift_repository
from app.repositories import shift_type_repository
from app.schemas import schemas
from app.services import calendar_service
from app.dependencies import requires_user
from app.structs.pages import CalendarMonthPage
from app.structs.structs import ScheduleRow, ShiftRow, UserRow

def month(
    request: Request,
    month: int,
    year: int,
    current_user=Depends(requires_user),
):
    """
    Handles requests related to viewing the calendar. \n
    Query params: day, simple \n
    Hx-request headers \n
    Render conditions:
        1. calendar view, standard request, whole page
        2. calendar view, hx-request, calendar partial
    Gaurd clauses:
        1. check for current user
        2. check if hx-request, calendar view, get all shifts
    Response Context:
        - request
        - current_user (always needed for header)
        - bae_user (always needed)
        - days_of_week (for calendar heading)
        - month_calendar (dictionary to hold calendar data)
        - current_date_object (used to track what day it currently is, useful for rendering related to holidays)
        - current_month_object (used to render the calendar)
        - prev_month_object
        - next_month_object
        - chat_data (optional, only if not hx-response)
    """
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
    # get user who shares their calendar with current user
    # find the DbShare where current user id is the receiver_id 
    # bae_user = db.query(DBUser).join(DbShare, DBUser.id == DbShare.sender_id).filter(
        # DbShare.receiver_id == current_user.id).first()
    
    # gathering user ids to query shift table and get shifts for both users at once
    # user_ids = [current_user.id]
    # if bae_user:
    #     user_ids.append(bae_user.id)
    
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
        shifts = [ShiftRow(*row) for row in cursor.fetchall()]

        # get current user bae_schedules for month
        cursor.execute("SELECT id, shift_id, user_id, date FROM schedules WHERE DATE(date) BETWEEN DATE(?) and DATE(?) AND user_id = ?;", (start_of_month, end_of_month, current_user[0]))
        schedules = [ScheduleRow(*row) for row in cursor.fetchall()]

        # get bae user shift types
        cursor.execute("SELECT id, long_name, short_name FROM shifts WHERE user_id = ?;", (bae_user.id,))
        bae_shifts = [ShiftRow(*row) for row in cursor.fetchall()]

        # get bae user schedules for month
        cursor.execute("SELECT id, shift_id, user_id, date FROM schedules WHERE DATE(date) BETWEEN DATE(?) and DATE(?) AND user_id = ?;", (start_of_month, end_of_month, bae_user.id))
        bae_schedules = [ScheduleRow(*row) for row in cursor.fetchall()]

    # repackage current user shifts as dict with shift ids as keys to access with .get()
    shifts_dict = {}
    for shift in shifts:
        shifts_dict[shift.id] = shift
        
    # repackage current user schedule as dict with dates as keys to access with .get()
    commitments = {}
    for commitment in schedules:
        date_key = commitment[3].split()[0]
        shift_id = commitment[1]
        commitments.setdefault(date_key, {})[shift_id] = commitment

    # repackage bae shifts as dict with shift ids as keys to access with .get()
    bae_shifts_dict = {}
    for shift in bae_shifts:
        bae_shifts_dict[shift.id] = shift

    for key, value in bae_shifts_dict.items():
        print("key", key)
        print("value", value)

    # repackage bae schedule as dict with dates as keys to access with .get()
    bae_commitments = {}
    for commitment in bae_schedules:
        date_key = commitment[3].split()[0]
        shift_id = commitment[1]
        bae_commitments.setdefault(date_key, {})[shift_id] = commitment

    for key, value in bae_commitments.items():
        print("key", key)
        print("value", value)


    context = CalendarMonthPage(
        current_user=current_user,
        days_of_week=calendar_service.DAYS_OF_WEEK,
        current_month=current_month_object,
        prev_month_object=prev_month_object,
        next_month_object=next_month_object,
        month_calendar=month_calendar_dict,
        shifts=shifts_dict,
        commitments=commitments,
        bae_shifts=bae_shifts_dict,
        bae_commitments=bae_commitments
    )

    response = templates.TemplateResponse(
        request=request,
        name="calendar/v2/index.html",
        context=context,
    )

    return response


def day(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    year: int,
    month: int,
    day: int
):
    return handle_get_calendar_day(request=request, current_user=current_user, year=year, month=month, day=day, db=db)


def get_calendar_day_edit(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    year: int,
    month: int,
    day: int
):
    return handle_get_calendar_day_edit(request=request, current_user=current_user, year=year, month=month, day=day, db=db)


def get_calendar_card_edit(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    date_string: str,
    shift_type_id: int,
):
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response
    # check if shift already exists
    # if exists delete, user will already have clicked a confirm on the frontend

    date_segments = date_string.split("-")
    db_shift = schemas.CreateShift(
        type_id=shift_type_id,
        user_id=current_user.id,
        date=datetime.datetime(int(date_segments[0]), int(
            date_segments[1]), int(date_segments[2]))
    )

    new_shift = shift_repository.create_shift(db=db, shift=db_shift)

    shift_type = shift_type_repository.get_user_shift_type(
        db=db, user_id=current_user.id, shift_type_id=shift_type_id)

    context = {
        "current_user": current_user,
        "request": request,
        "date_string": date_string,
        "shift_type": shift_type
    }

    return block_templates.TemplateResponse(
        name="/calendar/fragments/edit-view.html",
        context=context,
        block_name="shift_exists_button"
    )


async def delete_shift_for_date(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    date_string: str,
    shift_type_id: int,
):
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)

    # check if shift already exists
    # if exists delete, user will already have clicked a confirm on the frontend
    date_segments = date_string.split("-")
    date_object = datetime.datetime(
        int(date_segments[0]), int(date_segments[1]), int(date_segments[2]))

    existing_shift = shift_repository.get_user_shift(
        db=db, user_id=current_user.id, type_id=shift_type_id, date_object=date_object)

    if not existing_shift:
        return Response(status_code=404)

    shift_repository.delete_user_shift(db=db, shift_id=existing_shift.id)
    shift_type = shift_type_repository.get_user_shift_type(
        db=db, user_id=current_user.id, shift_type_id=shift_type_id)
    context = {
        "current_user": current_user,
        "request": request,
        "date_string": date_string,
        "shift_type": shift_type
    }

    return block_templates.TemplateResponse(
        name="/calendar/fragments/edit-view.html",
        context=context,
        block_name="no_shift_button"
    )
