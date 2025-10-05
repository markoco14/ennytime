
import sqlite3
from typing import Annotated, Optional
import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response, RedirectResponse

from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates, block_templates
from app.dependencies import requires_schedule_owner, requires_user
from app.models.user_model import DBUser
from app.schemas import schemas
from app.repositories import shift_repository, shift_type_repository
from app.services import calendar_service

router = APIRouter(prefix="/scheduling")

def index(
    request: Request,
    lite_user=Depends(requires_user),
):
    if not lite_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")
    
    current_time = datetime.datetime.now()

    # HX-Redirect required for hx-request
    if "hx-request" in request.headers:
        response = Response(status_code=303)
        response.headers["HX-Redirect"] = f"/scheduling/{current_time.year}/{current_time.month}"
        return response
    
    # Can use FastAPI Redirect with standard http request
    return RedirectResponse(status_code=303, url=f"/scheduling/{current_time.year}/{current_time.month}")
    
    
def month(
    request: Request,
    year: int,
    month: int,
    lite_user=Depends(requires_user),
):
    if not lite_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")
    
    context = {
        "current_user": lite_user
    }

    # need to handle the case where year and month are not provided
    current_date = datetime.date(year=year, month=month, day=1)

    prev_month_name, next_month_name = calendar_service.get_prev_and_next_month_names(
        current_month=month)

    month_calendar = calendar_service.get_month_date_list(year=year, month=month)

    # calendar_date_list is a list of dictionaries
    # the keys are date_strings to make matching shifts easier
    # ie; "2021-09-01": datetime.date()
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
            f"{year_string}-{month_string}-{day_string}": date_object
        }
        if date[1] == month:
            calendar_date_list.update(date_dict)

    # get the start and end of the month for query filters
    start_of_month = calendar_service.get_start_of_month(year=year, month=month)
    end_of_month = calendar_service.get_end_of_month(year=year, month=month)  

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()

        # get shift types
        cursor.execute("SELECT id, short_name FROM shifts WHERE user_id = ?;", (lite_user.id,))
        lite_shifts = cursor.fetchall()

        # get schedules for month
        cursor.execute("SELECT id, shift_id, user_id, date FROM schedules WHERE DATE(date) BETWEEN DATE(?) and DATE(?) AND user_id = ?;", (start_of_month, end_of_month, lite_user[0]))
        lite_schedule = cursor.fetchall()

    # repackage schedule as dict with dates as .get() accessible keys
    commitments = {}
    for commitment in lite_schedule:
        date_key = commitment[3].split()[0]
        shift_id = commitment[1]
        commitments.setdefault(date_key, {})[shift_id] = commitment

    context = {
        "request": request,
        "current_user": lite_user,
        "selected_month": month,
        "selected_month_name": current_date.strftime("%B"),
        "selected_year": year,
        "prev_month_name": prev_month_name,
        "next_month_name": next_month_name,
        "month_calendar": calendar_date_list,
        "lite_shifts": lite_shifts,
        "commitments": commitments
    }

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse(
            request=request,
            name="scheduling/fragments/schedule-list-oob.html",
            context=context
        )

    return templates.TemplateResponse(
        request=request,
        name="scheduling/index.html",
        context=context
    )


async def create(
    request: Request,
    lite_user=Depends(requires_user),
):
    if not lite_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")

    form_data = await request.form()
    date = form_data.get("date")
    date = f"{date} 00:00:00"
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO schedules (shift_id, user_id, date) VALUES (?, ?, ?)", (form_data.get("shift"), lite_user.id, date,))
        
    if request.headers.get("hx-request"):
        return Response(status_code=200, headers={"hx-refresh": "true"})
    else:
        return RedirectResponse(status_code=303, url="/scheduling")


async def delete(
    request: Request,
    schedule_id: int,
    lite_user=Depends(requires_schedule_owner)
):  
    if not lite_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")
        
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM schedules WHERE id = ?;", (schedule_id, ))
        
    if request.headers.get("hx-request"):
        return Response(status_code=200, headers={"hx-refresh": "true"})
    else:
        return RedirectResponse(status_code=303, url="/scheduling")