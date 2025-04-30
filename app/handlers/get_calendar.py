"""
Calendar related routes
"""
import logging
import datetime
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Request, Response
from fastapi.responses import RedirectResponse

from app.core.template_utils import templates
from app.models.share_model import DbShare
from app.models.user_model import DBUser
from app.queries import shift_queries
from app.repositories import shift_type_repository
from app.services import calendar_service, calendar_shift_service, chat_service


def handle_get_calendar(
    request: Request,
    current_user: DBUser,
    month: int,
    year: int,
    db: Session,
):
    """
    Handles requests related to viewing the calendar. \n
    Query params: day, simple \n
    Hx-request headers \n
    Render conditions:
        1. calendar view, standard request, whole page
        2. calendar view, hx-request, calendar partial
        3. calendar view, hx-request, simple view partial (animation: close modal and move back to calendar)
        4. detail view, standard request, whole page with modal open to detail view
        5. detail view, hx-request, detail view partial (animation: open modal and pop out of calendar)
        6. edit view, hx-request, edit view partial (animation: slide to edit view)
        7. edit view, standard request, whole page with modal open to edit view
    Only need to request shifts for whole month in conditions 1, 2, 4, and 7:
        1. Renders the whole page including the calendar so it needs all the shifts.
        2. Renders the calendar so it needs all the shifts.
        4. Renders the modal open but also renders the calendar behind it so it needs all the shifts.
        7. Renders the modal open but also renders the calendar behind it so it needs all the shifts
    Gaurd clauses:
        1. check for current user
        2. check if hx-request, day is selected, simple view
        3. check if hx-request, day is selected, detail view
        4. check if standard request, day is selected, detail view, get all the shifts
        5. check if hx-request, calendar view, get all shifts
        6. check if standard request, calender view, get all shifts
    """
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


    # get user who shares their calendar with current user
    # find the DbShare where current user id is the receiver_id 
    bae_user = db.query(DBUser).join(DbShare, DBUser.id == DbShare.sender_id).filter(
        DbShare.receiver_id == current_user.id).first()
    
    # gathering user ids to query shift table and get shifts for both users at once
    user_ids = [current_user.id]
    if bae_user:
        user_ids.append(bae_user.id)

    context = {
        "request": request,
        "current_user": current_user,
        "bae_user": bae_user,
        # "birthdays": birthdays,
        "current_day": current_day,
        "selected_month": selected_month,
        "selected_month_name": selected_month_name,
        "selected_year": selected_year,
    }
    
    month_calendar = calendar_service.get_month_calendar(
        year=selected_year, 
        month=selected_month
        )

    month_calendar_dict = dict(
        (str(day), {
            "date": day,
            "shifts": [],
            "bae_shifts": []
            }) for day in month_calendar)
    
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
    month_calendar_dict = calendar_shift_service.sort_shifts_by_user(
        all_shifts=all_shifts,
        month_calendar_dict=month_calendar_dict,
        current_user=current_user)
    
    # get previous and next month names for month navigation
    prev_month_name, next_month_name = calendar_service.get_prev_and_next_month_names(
        current_month=selected_month)

    context["days_of_week"] = calendar_service.DAYS_OF_WEEK
    context["month_calendar"] = month_calendar_dict
    context["prev_month_name"] = prev_month_name
    context["next_month_name"] = next_month_name
    
    # Slide to next month animation, change selected month, request whole calendar
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