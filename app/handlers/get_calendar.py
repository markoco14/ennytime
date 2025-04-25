"""
Calendar related routes
"""
import logging
import datetime
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import Request, Response
from fastapi.responses import RedirectResponse


from app.core.template_utils import templates
from app.models.share_model import DbShare
from app.models.user_model import DBUser
from app.queries import shift_queries
from app.services import calendar_service, calendar_shift_service, chat_service


def handle_get_calendar(
    request: Request,
    current_user: DBUser,
    month: int,
    year: int,
    db: Session,
    day: Optional[int] = None,
):
    if not current_user:
        if request.headers.get("HX-Request"):
            response = Response(status_code=401)
            response.headers["HX-Redirect"] = "/signin"
            response.delete_cookie("session-id")

            return response
        
        response = RedirectResponse(url="/signin", status_code=303)
        response.delete_cookie("session-id")

        return response
    
    current_time = datetime.datetime.now()
    current_day = current_time.day
    selected_year = year or current_time.year
    selected_month = month or current_time.month
    selected_month_name = calendar_service.MONTHS[selected_month - 1]

    # handle all birthday logic
    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=selected_month):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
        })

    # get user who shares their calendar with current user
    # find the DbShare where current user id is the receiver_id 
    bae_user = db.query(DBUser).join(DbShare, DBUser.id == DbShare.sender_id).filter(
        DbShare.receiver_id == current_user.id).first()

    if bae_user:
        if bae_user.has_birthday() and bae_user.birthday_in_current_month(current_month=selected_month):
            birthdays.append({
                "name": bae_user.display_name,
                "day": bae_user.birthday.day
            })

    # get previous and next month names for month navigation
    prev_month_name, next_month_name = calendar_service.get_prev_and_next_month_names(
        current_month=selected_month)

    month_calendar = calendar_service.get_month_calendar(
        year=selected_year, 
        month=selected_month
        )

    month_calendar_dict = dict((str(day), {"date": str(
        day), "day_number": day.day, "month_number": day.month, "shifts": [], "bae_shifts": []}) for day in month_calendar)

    
    # gathering user ids to query shift table and get shifts for both users at once
    user_ids = [current_user.id]
    if bae_user:
        user_ids.append(bae_user.id)

    # get the start and end of the month for query filters
    start_of_month = calendar_service.get_start_of_month(year=selected_year, month=selected_month)
    end_of_month = calendar_service.get_end_of_month(year=selected_year, month=selected_month)

    # get shifts for current user and bae user
    all_shifts = shift_queries.list_shifts_for_couple_by_month(
        db=db,
        user_ids=user_ids,
        start_of_month=start_of_month,
        end_of_month=end_of_month
        )
    
    # update the calendar dictionary with sorted shifts
    month_calendar_dict = calendar_shift_service.sort_shifts_by_user(all_shifts=all_shifts, month_calendar_dict=month_calendar_dict, current_user=current_user)

    context = {
        "request": request,
        "current_user": current_user,
        "birthdays": birthdays,
        "current_day": current_day,
        "selected_month": selected_month,
        "selected_month_name": selected_month_name,
        "selected_year": selected_year,
        "prev_month_name": prev_month_name,
        "next_month_name": next_month_name,
        "month_calendar": list(month_calendar_dict.values()),
        "days_of_week": calendar_service.DAYS_OF_WEEK,
    }

    if request.query_params.get("day") and "hx-request" in request.headers:
        response = templates.TemplateResponse(
            name="calendar/calendar-card-detail.html",
            context=context
        )

        return response
    
    if "hx-request" in request.headers:
        response = templates.TemplateResponse(
            name="calendar/fragments/calendar-oob.html",
            context=context,
        )
        return response
    

    # get chatroom id to link directly from the chat icon
    # get unread message count so chat icon can display the count on page load
    user_chat_data = chat_service.get_user_chat_data(
        db=db,
        current_user_id=current_user.id
    )

    context.update({"chat_data": user_chat_data})  
    response = templates.TemplateResponse(
        name="calendar/index.html",
        context=context,
    )

    return response