"""
Calendar related routes
"""
from typing import Annotated, Optional
from pprint import pprint
import datetime


from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse


from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates
from app.models.user_model import DBUser
from app.schemas import schemas
from app.repositories import share_repository, shift_repository
from app.repositories import shift_type_repository
from app.services import calendar_service


router = APIRouter()


@router.get("/calendar-card-simple/{date_string}", response_class=HTMLResponse)
def get_simple_calendar_day_card(
        request: Request,
        db: Annotated[Session, Depends(get_db)],
        date_string: str,
        current_user=Depends(auth_service.user_dependency)
):
    """Get calendar day card"""
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    year_number, month_number, day_number = calendar_service.extract_date_string_numbers(
        date_string=date_string)

    db_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=current_user.id)

    # only need to get an array of shifts
    # becauase only for one day, not getting whole calendar
    shifts = []
    for shift in db_shifts:
        if str(shift.date.date()) == date_string:
            shifts.append(shift._asdict())

    bae_shifts = []
    shared_with_me = share_repository.get_share_by_receiver_id(
        db=db, receiver_id=current_user.id)
    if shared_with_me:
        bae_db_shifts = shift_repository.get_user_shifts_details(
            db=db, user_id=shared_with_me.sender_id)
        for shift in bae_db_shifts:
            if str(shift.date.date()) == date_string:
                bae_shifts.append(shift)

    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=month_number):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
        })

    if shared_with_me:
        bae_user = share_repository.get_share_user_with_shifts_by_receiver_id(
            db=db, share_user_id=shared_with_me.sender_id)

        if bae_user.has_birthday() and bae_user.birthday_in_current_month(current_month=month_number):
            birthdays.append({
                "name": bae_user.display_name,
                "day": bae_user.birthday.day
            })

    context = {
        "request": request,
        "date": {
            "date": date_string,
            "shifts": shifts,
            "day_number": day_number,
            "bae_shifts": bae_shifts,
        },
        "current_user": current_user,
        "birthdays": birthdays
    }

    return templates.TemplateResponse(
        request=request,
        name="/calendar/calendar-card-simple.html",
        context=context,
    )


@router.get("/calendar-card-detail/{date_string}", response_class=HTMLResponse)
def get_calendar_card_detailed(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    date_string: str,
    current_user=Depends(auth_service.user_dependency)
):
    """Get calendar day card"""
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    # get the user's shifts
    user_shifts_query = text("""
        SELECT etime_shifts.*,
            etime_shift_types.long_name as long_name,
            etime_shift_types.short_name as short_name
        FROM etime_shifts
        LEFT JOIN etime_shift_types
        ON etime_shifts.type_id = etime_shift_types.id
        WHERE etime_shifts.user_id = :sender_id
        AND DATE(etime_shifts.date) = :date_string
        """)

    user_shifts_result = db.execute(
        user_shifts_query, {"sender_id": current_user.id, "date_string": date_string}).fetchall()

    year_number, month_number, day_number = calendar_service.extract_date_string_numbers(
        date_string)
    date = datetime.date(year_number, month_number, day_number)
    written_month = date.strftime("%B %d, %Y")
    written_day = date.strftime("%A")

    # check if anyone has shared their calendar with the current user
    share_query = text("""
        SELECT etime_shares.*,
            etime_users.display_name as bae_name
        FROM etime_shares
        LEFT JOIN etime_users ON etime_shares.sender_id = etime_users.id 
        WHERE etime_shares.receiver_id = :receiver_id
    """)

    share_result = db.execute(
        share_query, {"receiver_id": current_user.id}).fetchone()

    # organize birthdays
    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=month_number):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
        })
    if share_result:
        bae_user = share_repository.get_share_user_with_shifts_by_receiver_id(
            db=db, share_user_id=share_result.sender_id)

        if bae_user.has_birthday() and bae_user.birthday_in_current_month(current_month=month_number):
            birthdays.append({
                "name": bae_user.display_name,
                "day": bae_user.birthday.day
            })

    if not share_result:
        context = {
            "request": request,
            "current_user": current_user,
            "month": month_number,
            "written_month": written_month,
            "written_day": written_day,
            "date": {
                "date": date_string,
                "shifts": user_shifts_result,
                "day_number": day_number,
                "bae_shifts": [],
            },
            "birthdays": birthdays
        }

        return templates.TemplateResponse(
            request=request,
            name="/calendar/calendar-card-detail.html",
            context=context,
        )

    # if there is a share, get the sharing user's (bae's) shifts
    shifts_query = text("""
        SELECT etime_shifts.*,
            etime_shift_types.long_name as long_name,
            etime_shift_types.short_name as short_name
        FROM etime_shifts
        LEFT JOIN etime_shift_types
        ON etime_shifts.type_id = etime_shift_types.id
        WHERE etime_shifts.user_id = :sender_id
        AND DATE(etime_shifts.date) = :date_string
        """)

    shifts_result = db.execute(
        shifts_query, {"sender_id": share_result.sender_id, "date_string": date_string}).fetchall()

    context = {
        "request": request,
        "current_user": current_user,
        "bae_user": bae_user,
        "month": month_number,
        "written_month": written_month,
        "written_day": written_day,
        "date": {
            "date": date_string,
            "shifts": user_shifts_result,
            "day_number": day_number,
            "bae_shifts": shifts_result,
        },
        "birthdays": birthdays
    }

    return templates.TemplateResponse(
        request=request,
        name="/calendar/calendar-card-detail.html",
        context=context,
    )


@router.get("/calendar/card/{date_string}/edit")
def get_calendar_card_edit(
    request: Request,
    date_string: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
):
    db_shift_types = shift_type_repository.list_user_shift_types(db=db, user_id=current_user.id)

    query = text("""
        SELECT
            etime_shifts.*
        FROM etime_shifts
        WHERE etime_shifts.user_id = :user_id
        AND etime_shifts.date = :date_string
        ORDER BY etime_shifts.date
    """)

    result = db.execute(
        query,
        {"user_id": current_user.id,
         "date_string": date_string
         }
    ).fetchall()

    user_shifts = []
    for row in result:
        user_shifts.append(row._asdict())

    context= {
        "request": request,
        "current_user": current_user,
        "shifts": user_shifts,
        "shift_types": db_shift_types,
        "date_string": date_string
    }

    return templates.TemplateResponse(
        name="/calendar/fragments/edit-schedule.html",
        context=context
    )


@router.get("/add-shift-form/{date_string}", response_class=HTMLResponse)
def get_calendar_day_form(
    request: Request,
    date_string: str,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency)
):
    """Get calendar day form"""
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    shift_types = shift_type_repository.list_user_shift_types(
        db=db,
        user_id=current_user.id)

    # TODO: Get the day of the week

    # TODO: Get the current user shifts for this day
    query = text("""
        SELECT
            etime_shifts.*
        FROM etime_shifts
        WHERE etime_shifts.user_id = :user_id
        AND etime_shifts.date = :date_string
        ORDER BY etime_shifts.date
    """)

    result = db.execute(
        query,
        {"user_id": current_user.id,
         "date_string": date_string
         }
    ).fetchall()

    user_shifts = []
    for row in result:
        user_shifts.append(row._asdict())

    year_number, month_number, day_number = calendar_service.extract_date_string_numbers(
        date_string=date_string)
    date = datetime.date(year_number, month_number, day_number)
    written_month = date.strftime("%B %d, %Y")
    written_day = date.strftime("%A")

    date_dict = {
        "date_string": date_string,
        "day_of_week": str(calendar_service.get_weekday(date_string)),
        "shifts": user_shifts,
    }

    context = {
        "current_user": current_user,
        "request": request,
        "shift_types": shift_types,
        "day_number": day_number,
        "date_string": date_string,
        "written_month": written_month,
        "written_day": written_day,
        "date_dict": date_dict,
    }

    if not shift_types:
        return templates.TemplateResponse(
            request=request,
            name="/calendar/calendar-card-no-types.html",
            context=context
        )

    return templates.TemplateResponse(
        request=request,
        name="/calendar/fragments/edit-schedule.html",
        context=context
    )

