
from typing import Annotated
import datetime
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates, block_templates
from app.models.user_model import DBUser
from app.schemas import schemas
from app.repositories import shift_repository, shift_type_repository, share_repository, user_repository
from app.services import calendar_service, chat_service

router = APIRouter()

@router.get("/scheduling", response_class=HTMLResponse)
def get_scheduling_index_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    year: int = None,
    month: int = None,
):
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response
    
    # need to handle the case where year and month are not provided
    current_time = datetime.datetime.now()
    if not year:
        year = current_time.year
    if not month:
        month = current_time.month

    month_calendar = calendar_service.get_month_date_list(
        year=year,
        month=month
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
        date_dict = {
            f"{year_string}-{month_string}-{day_string}": {
                "date_string": f"{year_string}-{month_string}-{day_string}",
                "day_of_week": str(calendar_service.Weekday(date[3])),
            }
        }
        if date[1] == month:
            calendar_date_list.update(date_dict)

    shift_types = shift_type_repository.list_user_shift_types(
        db=db, user_id=current_user.id)

    # get the start and end of the month for query filters
    start_of_month = datetime.datetime(year, month, 1)
    end_of_month = datetime.datetime(
        year, month + 1, 1) + datetime.timedelta(seconds=-1)

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

    # get unread message count so chat icon can display the count on page load
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "current_month": month,
        "month_calendar": calendar_date_list,
        "shift_types": shift_types,
        "user_shifts": user_shifts,
        "message_count": message_count
    }

    return block_templates.TemplateResponse(
        name="webapp/shifts/add-shifts-page.html",
        context=context
    )

