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
    day: Optional[int] = None,
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

    month_calendar_dict = dict(
        (str(day), {
            "date": day,
            "shifts": [],
            "bae_shifts": []
            }) for day in month_calendar)

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
        "month_calendar": month_calendar_dict,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
    }

    # Return to calendar animation, closed modal, and request simple calendar card for selected day
    if "hx-request" in request.headers and request.query_params.get("day") and request.query_params.get("simple"):
        date_object = datetime.date(year=year, month=month, day=day)
        context["date_object"] = date_object

        if not bae_user:
            db_user_shifts = shift_queries.list_shifts_for_user_by_date(
                db=db,
                user_id=current_user.id,
                selected_date = date_object.strftime("%Y-%m-%d")
            )
            user_shifts = user_shifts = [shift[0] for shift in db_user_shifts if shift[0].user_id == current_user.id]
            bae_shifts = []
        else:
            shifts_for_couple = shift_queries.list_shifts_for_couple_by_date(
                                                    db=db,
                                                    user_ids=[current_user.id, bae_user.id],
                                                    selected_date = date_object.strftime("%Y-%m-%d")
                                                    )

            user_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == current_user.id]
            bae_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == bae_user.id]

        context["value"] = {
            "date": date_object,
            "shifts": user_shifts,
            "bae_shifts": bae_shifts
        }

        response = templates.TemplateResponse(
            name="calendar/calendar-card-simple.html",
            context=context
        )

        response.headers["HX-Push-Url"] = f"/calendar/{date_object.year}/{date_object.month}"

        return response
    
    # Slide to edit view animation, request edit view
    if "hx-request" in request.headers and request.query_params.get("day") and request.query_params.get("edit"):
        date_object = datetime.date(year=year, month=month, day=day)
        context["date_object"] = date_object

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
            "date_string": date_object.strftime("%Y-%m-%d")
            }
        ).fetchall()

        user_shifts = []
        for row in result:
            user_shifts.append(row._asdict())

        context["shifts"] = user_shifts
        context["shift_types"] = db_shift_types
        context["date_string"] = date_object.strftime("%Y-%m-%d")

        response = templates.TemplateResponse(
            name="calendar/fragments/edit-view-oob.html",
            context=context
        )

        response.headers["HX-Push-Url"] = f"/calendar/{date_object.year}/{date_object.month}?day={day}&edit=true"

        return response
    
    # Open modal animation, request detail card for selected day
    if "hx-request" in request.headers and request.query_params.get("day"):
        date_object = datetime.date(year=year, month=month, day=day)

        context["date_object"] = date_object
        context["bae_user"] = bae_user

        if not bae_user:
            db_user_shifts = shift_queries.list_shifts_for_user_by_date(
                db=db,
                user_id=current_user.id,
                selected_date = date_object.strftime("%Y-%m-%d")
            )
            user_shifts = user_shifts = [shift[0] for shift in db_user_shifts if shift[0].user_id == current_user.id]
            bae_shifts = []
        else:
            shifts_for_couple = shift_queries.list_shifts_for_couple_by_date(
                                                    db=db,
                                                    user_ids=[current_user.id, bae_user.id],
                                                    selected_date = date_object.strftime("%Y-%m-%d")
                                                    )

            user_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == current_user.id]
            bae_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == bae_user.id]

        context["user_shifts"] = user_shifts
        context["bae_shifts"] = bae_shifts

        if "&edit=true" in request.headers["referer"]:
            response = templates.TemplateResponse(
                name="calendar/fragments/detail-view-oob.html",
                context=context
            )

            response.headers["Hx-Push-Url"] = f"/calendar/{date_object.year}/{date_object.month}?day={date_object.day}"

            return response        

        response = templates.TemplateResponse(
            name="calendar/calendar-card-detail.html",
            context=context
        )

        return response
    
    # Full page refresh, modal open, request whole calendar, render details in modal for selected day
    if request.query_params.get("day") and request.query_params.get("edit"):
        date_object = datetime.date(year=selected_year, month=selected_month, day=day)
        user_chat_data = chat_service.get_user_chat_data(
            db=db,
            current_user_id=current_user.id
        )

        context.update({"chat_data": user_chat_data})
        context["date_object"] = date_object
        context["bae_user"] = bae_user

        if not bae_user:
            db_user_shifts = shift_queries.list_shifts_for_user_by_date(
                db=db,
                user_id=current_user.id,
                selected_date = date_object.strftime("%Y-%m-%d")
            )
            user_shifts = user_shifts = [shift[0] for shift in db_user_shifts if shift[0].user_id == current_user.id]
            bae_shifts = []
        else:
            shifts_for_couple = shift_queries.list_shifts_for_couple_by_date(
                                                    db=db,
                                                    user_ids=[current_user.id, bae_user.id],
                                                    selected_date = date_object.strftime("%Y-%m-%d")
                                                    )

            user_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == current_user.id]
            bae_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == bae_user.id]

        context["user_shifts"] = user_shifts
        context["bae_shifts"] = bae_shifts

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
            "date_string": date_object.strftime("%Y-%m-%d")
            }
        ).fetchall()

        user_shifts = []
        for row in result:
            user_shifts.append(row._asdict())

        context["shifts"] = user_shifts
        context["shift_types"] = db_shift_types
        context["date_string"] = date_object.strftime("%Y-%m-%d")

        response = templates.TemplateResponse(
            name="calendar/index.html",
            context=context,
        )
        return response
    
    # Full page refresh, modal open, request whole calendar, render details in modal for selected day
    if request.query_params.get("day"):
        date_object = datetime.date(year=selected_year, month=selected_month, day=day)
        user_chat_data = chat_service.get_user_chat_data(
            db=db,
            current_user_id=current_user.id
        )

        context.update({"chat_data": user_chat_data})
        context["date_object"] = date_object
        context["bae_user"] = bae_user

        if not bae_user:
            db_user_shifts = shift_queries.list_shifts_for_user_by_date(
                db=db,
                user_id=current_user.id,
                selected_date = date_object.strftime("%Y-%m-%d")
            )
            user_shifts = user_shifts = [shift[0] for shift in db_user_shifts if shift[0].user_id == current_user.id]
            bae_shifts = []
        else:
            shifts_for_couple = shift_queries.list_shifts_for_couple_by_date(
                                                    db=db,
                                                    user_ids=[current_user.id, bae_user.id],
                                                    selected_date = date_object.strftime("%Y-%m-%d")
                                                    )

            user_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == current_user.id]
            bae_shifts = [shift[0] for shift in shifts_for_couple if shift[0].user_id == bae_user.id]

        context["user_shifts"] = user_shifts
        context["bae_shifts"] = bae_shifts

        response = templates.TemplateResponse(
            name="calendar/index.html",
            context=context,
        )
        return response
    
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