
from typing import Annotated, Optional
import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response, RedirectResponse

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates, block_templates
from app.models.user_model import DBUser
from app.schemas import schemas
from app.repositories import shift_repository, shift_type_repository
from app.services import calendar_service, chat_service

router = APIRouter(prefix="/scheduling")

def index(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    year: Optional[int] = None,
    month: Optional[int] = None,
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response
    
    current_time = datetime.datetime.now()
    selected_year = year or current_time.year
    selected_month = month or current_time.month
    
    # HX-Redirect required for hx-request
    if "hx-request" in request.headers:
        response = Response(status_code=303)
        response.headers["HX-Redirect"] = f"/scheduling/{selected_year}/{selected_month}"
        return response
    
    # Can use FastAPI Redirect with standard http request
    return RedirectResponse(status_code=303, url=f"/scheduling/{selected_year}/{selected_month}")
    
    
def month(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    year: Optional[int] = None,
    month: Optional[int] = None,
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response
    
    context = {
        "request": request,
        "current_user": current_user
    }

    # TODO: check first if there are any shift types.
    shift_types = shift_type_repository.list_user_shift_types(
        db=db, user_id=current_user.id)
    if not shift_types:
        response = RedirectResponse(status_code=303, url="/shifts/setup") 
        return response
    
    # TODO:if no shift types, return page with shift type form or info about

    # TODO: if shift types send the page
    
    # need to handle the case where year and month are not provided
    current_time = datetime.datetime.now()
    selected_year = year or current_time.year
    selected_month = month or current_time.month
    selected_month_name = calendar_service.MONTHS[selected_month - 1]

    prev_month_name, next_month_name = calendar_service.get_prev_and_next_month_names(
        current_month=selected_month)

    month_calendar = calendar_service.get_month_date_list(
        year=selected_year,
        month=selected_month
    )

    # calendar_date_list is a list of dictionaries
    # the keys are date_strings to make matching shifts easier
    # ie; "2021-09-01": {"more keys": "more values"}
    calendar_date_list = {}

    # because month calendar year/month/day are numbers
    # numbers less than 10 don't have preceeding 0's to match the formatting of
    # the date strings, need to add 0's to the front of the numbers
    for date in month_calendar:
        year_string = f"{date[0]}"
        month_string = f"{date[1]}"
        day_string = f"{date[2]}"
        if date[1] < 10:
            month_string = f"0{date[1]}"
        if date[2] < 10:
            day_string = f"0{date[2]}"
        
        date_object = datetime.date(year=date[0], month=date[1], day=date[2])
        date_dict = {
            f"{year_string}-{month_string}-{day_string}": {
                "date_string": f"{date_object.year}-{month_string}-{day_string}",
                "day_of_week": str(calendar_service.Weekday(date[3])),
                "date_object": date_object
            }
        }
        if date[1] == selected_month:
            calendar_date_list.update(date_dict)

    # get the start and end of the month for query filters
    start_of_month = calendar_service.get_start_of_month(year=selected_year, month=selected_month)
    end_of_month = calendar_service.get_end_of_month(year=selected_year, month=selected_month)

    query = text("""
        SELECT
            etime_shifts.*
        FROM etime_shifts
        WHERE etime_shifts.user_id = :user_id
        AND etime_shifts.date >= :start_of_month
        AND etime_shifts.date <= :end_of_month
        ORDER BY etime_shifts.date
    """)

    result = db.execute(
        query,
        {"user_id": current_user.id,
         "start_of_month": start_of_month,
         "end_of_month": end_of_month}
    ).fetchall()
    user_shifts = []
    for row in result:
        user_shifts.append(row._asdict())

    # here is the problem
    # overwriting the previous shift when there are 2
    # only 1 being packed and sent
    for shift in user_shifts:
        key_to_find = f"{shift['date'].date()}"
        if key_to_find in calendar_date_list:
            if not calendar_date_list[f"{key_to_find}"].get("shifts"):
                calendar_date_list[f"{key_to_find}"]["shifts"] = []

            calendar_date_list[f"{key_to_find}"]["shifts"].append(shift)

    # get chatroom id to link directly from the chat icon
    # get unread message count so chat icon can display the count on page load
    user_chat_data = chat_service.get_user_chat_data(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "selected_month": selected_month,
        "selected_month_name": selected_month_name,
        "selected_year": selected_year,
        "prev_month_name": prev_month_name,
        "next_month_name": next_month_name,
        "month_calendar": calendar_date_list,
        "shift_types": shift_types,
        "user_shifts": user_shifts,
        "chat_data": user_chat_data
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            name="scheduling/fragments/schedule-list-oob.html",
            context=context
        )


    return templates.TemplateResponse(
        name="scheduling/index.html",
        context=context
    )


async def create(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    date: str,
    type_id: int
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

    date_segments = date.split("-")
    db_shift = schemas.CreateShift(
        type_id=type_id,
        user_id=current_user.id,
        date=datetime.datetime(int(date_segments[0]), int(
            date_segments[1]), int(date_segments[2]))
    )

    new_shift = shift_repository.create_shift(db=db, shift=db_shift)

    shift_type = shift_type_repository.get_user_shift_type(
        db=db, user_id=current_user.id, shift_type_id=type_id)

    context = {
        "current_user": current_user,
        "request": request,
        "date": {"date_string": date},
        "shifts": [new_shift],
        "type": shift_type
    }

    return templates.TemplateResponse(
        name="/scheduling/fragments/shift-exists-button.html",
        context=context,
    )


async def delete(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    date: str,
    type_id: int
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
    date_segments = date.split("-")
    date_object = datetime.datetime(
        int(date_segments[0]), int(date_segments[1]), int(date_segments[2]))

    existing_shift = shift_repository.get_user_shift(
        db=db, user_id=current_user.id, type_id=type_id, date_object=date_object)

    if not existing_shift:
        return Response(status_code=404)

    shift_repository.delete_user_shift(db=db, shift_id=existing_shift.id)
    shift_type = shift_type_repository.get_user_shift_type(
        db=db, user_id=current_user.id, shift_type_id=type_id)
    context = {
        "current_user": current_user,
        "request": request,
        "date": {"date_string": date},
        "type": shift_type
    }

    return block_templates.TemplateResponse(
        name="scheduling/fragments/no-shift-button.html",
        context=context,
    )
