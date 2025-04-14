"""
Calendar related routes
"""
import logging


from fastapi import Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.core.template_utils import templates, block_templates
from app.models.user_model import DBUser
from app.repositories import share_repository, shift_repository
from app.services import calendar_service

def handle_get_calendar_card_simple(request: Request, current_user: DBUser, date_string: str, db: Session):
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
        "selected_month": month_number,
        "current_user": current_user,
        "birthdays": birthdays
    }

    return templates.TemplateResponse(
        request=request,
        name="/calendar/calendar-card-simple.html",
        context=context,
    )