import logging
import time
from typing import Annotated, Optional
from pprint import pprint
import datetime


from pydantic import BaseModel
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse


from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates, block_templates
from app.handlers.get_calendar import handle_get_calendar
from app.handlers.get_calendar_card_simple import handle_get_calendar_card_simple
from app.models.db_shift import DbShift
from app.models.db_shift_type import DbShiftType
from app.models.share_model import DbShare
from app.models.user_model import DBUser
from app.queries import shift_queries
from app.repositories import share_repository, shift_repository
from app.repositories import shift_type_repository
from app.schemas import schemas
from app.services import calendar_service, calendar_shift_service, chat_service


def handle_get_calendar_card_detail(request: Request, current_user: DBUser, date_string: str, db: Session):
    """Get calendar day card"""
    if not current_user:
        if request.headers.get("HX-Request"):
            response = Response(status_code=401)
            response.headers["HX-Redirect"] = "/signin"
            response.delete_cookie("session-id")

            return response
        
        response = RedirectResponse(url="/signin", status_code=303)
        response.delete_cookie("session-id")

        return response
    
    db_trips = 0

    year_number, month_number, day_number = calendar_service.extract_date_string_numbers(
        date_string)
    date = datetime.date(year_number, month_number, day_number)
    written_month = date.strftime("%B %d, %Y")
    written_day = date.strftime("%A")

     # directly get the bae user now.
    direct_bae_user_start = time.perf_counter()
    direct_bae_user = db.query(DBUser
                                ).join(DbShare, DBUser.id == DbShare.sender_id
                                ).filter(DbShare.receiver_id == current_user.id
                                ).first()
    direct_bae_user_time = time.perf_counter() - direct_bae_user_start
    db_trips += 1

    # organize birthdays
    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=month_number):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
        })

    if direct_bae_user and direct_bae_user.has_birthday() and direct_bae_user.birthday_in_current_month(current_month=month_number):
        birthdays.append({
            "name": direct_bae_user.display_name,
            "day": direct_bae_user.birthday.day
        })

    if not direct_bae_user:
        # query 1 - get the current user's shifts
        get_current_user_shifts_start = time.perf_counter()
        direct_current_user_shifts = shift_queries.list_shifts_for_user_by_date(
            db=db,
            user_id=current_user.id,
            selected_date=date_string
        )
        get_current_user_shifts_time = time.perf_counter() - get_current_user_shifts_start
        db_trips += 1

        user_shifts_with_type = []
        for shift, shift_type in direct_current_user_shifts:
            shift_with_type =schemas.ShiftWithType(
                id=shift.id,
                type_id=shift.type_id,
                user_id=shift.user_id,
                date=shift.date,
                long_name=shift_type.long_name,
                short_name=shift_type.short_name
            ) 
            user_shifts_with_type.append(shift_with_type)

        context = {
            "request": request,
            "current_user": current_user,
            "month": month_number,
            "written_month": written_month,
            "written_day": written_day,
            "date": {
                "date": date_string,
                "shifts": user_shifts_with_type,
                "day_number": day_number,
                "bae_shifts": [],
            },
            "selected_month": month_number,
            "birthdays": birthdays
        }

        logging.info(f"User: No bae user found.")
        logging.info(f"Total number of db trips is {db_trips} ({db_trips + 1} with user dep).")
        logging.info(f"User: Total time for get user shifts is {get_current_user_shifts_time} seconds.")

        return templates.TemplateResponse(
            request=request,
            name="/calendar/calendar-card-detail.html",
            context=context,
        )
    
    get_both_user_shifts_start = time.perf_counter()
    shifts_for_couple = shift_queries.list_shifts_for_couple_by_date(
                                                    db=db,
                                                    user_ids=[current_user.id, direct_bae_user.id],
                                                    selected_date = date_string
                                                    )
    get_both_user_shifts_time = time.perf_counter() - get_both_user_shifts_start
    db_trips += 1

    prepared_current_user_shifts = []
    prepared_bae_user_shifts = []
    for shift, shift_tpye in shifts_for_couple:
        if shift.user_id == current_user.id:
            prepared_current_user_shifts.append(schemas.ShiftWithType(
                id=shift.id,
                type_id=shift.type_id,
                user_id=shift.user_id,
                date=shift.date,
                long_name=shift_tpye.long_name,
                short_name=shift_tpye.short_name
            ))
        if shift.user_id == direct_bae_user.id:
            prepared_bae_user_shifts.append(schemas.ShiftWithType(
                id=shift.id,
                type_id=shift.type_id,
                user_id=shift.user_id,
                date=shift.date,
                long_name=shift_tpye.long_name,
                short_name=shift_tpye.short_name
            ))

    context = {
        "request": request,
        "current_user": current_user,
        "bae_user": direct_bae_user,
        "month": month_number,
        "written_month": written_month,
        "written_day": written_day,
        "date": {
            "date": date_string,
            "shifts": prepared_current_user_shifts,
            "day_number": day_number,
            "bae_shifts": prepared_bae_user_shifts,
        },
        "selected_month": month_number,
        "birthdays": birthdays
    }

    logging.info(f"Total number of db trips is {db_trips} ({db_trips + 1} with user dep).")
    logging.info(f"Total time for db trips is {direct_bae_user_time + get_both_user_shifts_time} seconds.")
    logging.info(f"User: Total time for get bae user is {direct_bae_user_time} seconds.")
    logging.info(f"User: Total time for get both user shifts is {get_both_user_shifts_time} seconds.")

    return templates.TemplateResponse(
        request=request,
        name="/calendar/calendar-card-detail.html",
        context=context,
    )