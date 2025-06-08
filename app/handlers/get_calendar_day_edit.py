"""
Calendar related routes
"""
import logging
import datetime

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


def handle_get_calendar_day_edit(
    request: Request,
    current_user: DBUser,
    year: int,
    month: int,
    day: int,
    db: Session,
):
    """
        Handles requests related to viewing a selected day on the calendar.\n
        Render conditions:
            1. edit view, hx-request, animation: slide to edit view
            2. edit view, standard request, whole page with modal open to edit view
        Gaurd clauses:
            1. check for current user (denies access if no user)
            2. check if hx-request (only renders edit view oob)
        Base condition is render whole calendar with modal open and set to edit view
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
    selected_date_object = datetime.date(year=year, month=month, day=day)
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

    # Slide to edit view animation, request edit view
    if "hx-request" in request.headers:
        """Response context:
            - request
            - current_user
            - bae_user
            - selected_month (holds the selected month, might not be necessary)
            - selected_date_object (date constructed from current year, month, day)
            - shifts
            - shift_types
            - date_string
            """
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
            "date_string": selected_date_object.strftime("%Y-%m-%d")
            }
        ).fetchall()

        user_shifts = []
        for row in result:
            user_shifts.append(row._asdict())

        context = {
            "request": request,
            "current_user": current_user,
            "bae_user": bae_user,
            "selected_date_object": selected_date_object,
            "shifts": user_shifts,
            "shift_types": db_shift_types,
            "date_string": selected_date_object.strftime("%Y-%m-%d")
        }

        response = templates.TemplateResponse(
            name="calendar/fragments/edit-view-oob.html",
            context=context
        )

        return response
    
    """Response context:
        - request
        - current_user
        - bae_user
        - selected_month (holds the selected month, might not be necessary)
        - current_day
        - selected_month_name
        - selected_year
        - days_of_week
        - month_calendar
        - prev_month_name
        - next_month_name
        """
    
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
    
    # Full page refresh, modal open, request whole calendar, render details in modal for selected day
    selected_date_object = datetime.date(year=current_month_object.year, month=current_month_object.month, day=day)
    user_chat_data = chat_service.get_user_chat_data(
        db=db,
        current_user_id=current_user.id
    )

    if not bae_user:
        db_user_shifts = shift_queries.list_shifts_for_user_by_date(
            db=db,
            user_id=current_user.id,
            selected_date = selected_date_object.strftime("%Y-%m-%d")
        )
        user_shifts = user_shifts = [shift[0] for shift in db_user_shifts if shift[0].user_id == current_user.id]
        bae_shifts = []
    else:
        shifts_for_couple = shift_queries.list_shifts_for_couple_by_date(
                                                db=db,
                                                user_ids=[current_user.id, bae_user.id],
                                                selected_date = selected_date_object.strftime("%Y-%m-%d")
                                                )

        user_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == current_user.id]
        bae_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == bae_user.id]

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
        "date_string": selected_date_object.strftime("%Y-%m-%d")
        }
    ).fetchall()

    user_shifts = []
    for row in result:
        user_shifts.append(row._asdict())

    context = {
        "request": request,
        "current_user": current_user,
        "bae_user": bae_user,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "month_calendar": month_calendar_dict,
        "selected_date_object": selected_date_object,
        "current_month_object": current_month_object,
        "prev_month_object": prev_month_object,
        "next_month_object": next_month_object,
        "chat_data": user_chat_data,
        "user_shifts": user_shifts,
        "bae_shifts": bae_shifts,
        "shifts": user_shifts,
        "shift_types": db_shift_types,
        "date_string": selected_date_object.strftime("%Y-%m-%d")
    }

    response = templates.TemplateResponse(
        name="calendar/index.html",
        context=context,
    )
    return response

