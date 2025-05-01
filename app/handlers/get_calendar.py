"""
Calendar related routes
"""
import datetime

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
    year: int,
    month: int,
    db: Session,
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
        if request.headers.get("HX-Request"):
            response = Response(status_code=401)
            response.headers["HX-Redirect"] = "/signin"
            response.delete_cookie("session-id")

            return response
        
        response = RedirectResponse(url="/signin", status_code=303)
        response.delete_cookie("session-id")

        return response
    
    current_date_object = datetime.datetime.now()
    current_month_object = datetime.date(year=year, month=month, day=1)
    prev_month_object = datetime.date(year=year if month != 1 else year - 1, month=month - 1 if month != 1 else 12, day=1)
    next_month_object = datetime.date(year=year if month != 12 else year + 1, month=month + 1 if month != 12 else 1, day=1)
    
    # get user who shares their calendar with current user
    # find the DbShare where current user id is the receiver_id 
    bae_user = db.query(DBUser).join(DbShare, DBUser.id == DbShare.sender_id).filter(
        DbShare.receiver_id == current_user.id).first()
    
    # gathering user ids to query shift table and get shifts for both users at once
    user_ids = [current_user.id]
    if bae_user:
        user_ids.append(bae_user.id)
    
    month_calendar = calendar_service.get_month_calendar(
        year=current_month_object.year, 
        month=current_month_object.month
        )

    month_calendar_dict = dict(
        (str(day), {
            "date": day,
            "shifts": [],
            "bae_shifts": []
            }) for day in month_calendar)
    
    # get the start and end of the month for query filters
    start_of_month = calendar_service.get_start_of_month(year=current_month_object.year, month=current_month_object.month)
    end_of_month = calendar_service.get_end_of_month(year=current_month_object.year, month=current_month_object.month)

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
    
    context = {
        "request": request,
        "current_user": current_user,
        "bae_user": bae_user,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "month_calendar": month_calendar_dict,
        "current_date_object": current_date_object,
        "current_month_object": current_month_object,
        "prev_month_object": prev_month_object,
        "next_month_object": next_month_object,
    }

    # Slide to next month animation, change selected month, request whole calendar
    if "hx-request" in request.headers:
        """No chat data needed because partial response"""
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