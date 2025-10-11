
import sqlite3
import datetime

from fastapi import Depends, Request
from fastapi.responses import Response, RedirectResponse

from app.core.template_utils import templates
from app.dependencies import requires_schedule_owner, requires_user
from app.services import calendar_service
from app.structs.pages import NoShiftBtn, ScheduleMonthPage, YesShiftBtn
from app.viewmodels.structs import ScheduleRow, ShiftRow


def index(
    request: Request,
    current_user=Depends(requires_user),
):
    if not current_user:
        if request.headers.get("hx-request"):
            response = Response(status_code=200, headers={"hx-redirect": f"/signin"})
        else:
            response = RedirectResponse(status_code=303, url=f"/signin")
        response.delete_cookie("session-id")
        return response
    
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
    current_user=Depends(requires_user),
):
    if not current_user:
        if request.headers.get("hx-request"):
            response = Response(status_code=200, headers={"hx-redirect": f"/signin"})
        else:
            response = RedirectResponse(status_code=303, url=f"/signin")
        response.delete_cookie("session-id")
        return response
    
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
        cursor.execute("SELECT id, long_name, short_name FROM shifts WHERE user_id = ?;", (current_user.id,))
        shift_rows = [ShiftRow(*row) for row in cursor.fetchall()]

        # get schedules for month
        cursor.execute("SELECT id, shift_id, user_id, date FROM schedules WHERE DATE(date) BETWEEN DATE(?) and DATE(?) AND user_id = ?;", (start_of_month, end_of_month, current_user.id))
        schedule_rows = [ScheduleRow(*row) for row in cursor.fetchall()]

    # don't need to package shifts the same way as in calendar
    # rendering directly from a list is fine

    # repackage schedule as dict with dates as .get() accessible keys
    schedules = {}
    for schedule in schedule_rows:
        date_key = schedule[3].split()[0]
        shift_id = schedule[1]
        schedules.setdefault(date_key, {})[shift_id] = schedule

    context = ScheduleMonthPage(
        current_date=current_date,
        current_user=current_user,
        prev_month_name=prev_month_name,
        next_month_name=next_month_name,
        month_calendar=calendar_date_list,
        shifts=shift_rows,
        schedules=schedules
    )

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
    current_user=Depends(requires_user),
):  
    if not current_user:
        if request.headers.get("hx-request"):
            response = Response(status_code=200, headers={"hx-redirect": f"/signin"})
        else:
            response = RedirectResponse(status_code=303, url=f"/signin")
        response.delete_cookie("session-id")
        return response

    form_data = await request.form()
    date = form_data.get("date")
    date = f"{date} 00:00:00"
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO schedules (shift_id, user_id, date) VALUES (?, ?, ?);", (form_data.get("shift"), current_user.id, date,))
        row_id = cursor.lastrowid
        schedule_row = ScheduleRow(id=row_id, shift_id=form_data.get("shift"), user_id=current_user.id, date=date)
        
    if request.headers.get("hx-request"):
        with sqlite3.connect("db.sqlite3") as conn:
                conn.execute("PRAGMA foreign_keys=ON;")
                cursor = conn.cursor()
                cursor.execute("SELECT id, long_name, short_name FROM shifts WHERE id = ?;", (form_data.get("shift"), ))
                shift_row = ShiftRow(*cursor.fetchone())

        return templates.TemplateResponse(
            request=request,
            name="scheduling/fragments/shift-exists-button.html",
            context=YesShiftBtn(
                shift=shift_row,
                schedule=schedule_row
            )
        )
    else:
        return RedirectResponse(status_code=303, url="/scheduling")


async def delete(
    request: Request,
    schedule_id: int,
    current_user=Depends(requires_schedule_owner)
):  
    if not current_user:
        if request.headers.get("hx-request"):
            response = Response(status_code=200, headers={"hx-redirect": f"/signin"})
        else:
            response = RedirectResponse(status_code=303, url=f"/signin")
        response.delete_cookie("session-id")
        return response
        
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()

        cursor.execute("SELECT id, shift_id, user_id, date FROM schedules WHERE id = ?;", (schedule_id, ))
        schedule_row = ScheduleRow(*cursor.fetchone())

        cursor.execute("DELETE FROM schedules WHERE id = ?;", (schedule_id, ))
    
    if request.headers.get("hx-request"):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("SELECT id, long_name, short_name FROM shifts WHERE id =?;", (schedule_row[1], ))
            shift_row = ShiftRow(*cursor.fetchone())

        date_obj = datetime.datetime.strptime(schedule_row[3], "%Y-%m-%d %H:%M:%S").date()

        response = templates.TemplateResponse(
            request=request,
            name="scheduling/fragments/no-shift-button.html",
            context=NoShiftBtn(
                date=date_obj,
                shift=shift_row
            )
        )

        return response
    else:
        return RedirectResponse(status_code=303, url="/scheduling")