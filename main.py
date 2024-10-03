"""Main file to hold app and api routes"""
import datetime
from typing import Annotated, Optional
from pprint import pprint
import time
from fastapi import Depends, FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from mangum import Mangum
from sqlalchemy import text
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from app.auth import auth_router, auth_service
from app.core.database import get_db
from app.core.config import get_settings
from app.core.template_utils import templates
from app.repositories import user_repository, shift_type_repository
from app.routers import (
    admin_router,
    calendar_router,
    profile_router,
    share_router,
    shift_router,
    chat_router,
    scheduling_router
)
from app.schemas import schemas
from app.services import calendar_service, chat_service
from app.models.user_model import DBUser
from app.models.share_model import DbShare
from app.models.db_shift import DbShift
from app.models.db_shift_type import DbShiftType


SETTINGS = get_settings()


app = FastAPI()


class ClosingDownMiddleware(BaseHTTPMiddleware):
    async def dispatch(
            self,
            request: Request,
            call_next: RequestResponseEndpoint
    ):
        if SETTINGS.CLOSED_DOWN == "true":
            context = {"request": request}
            return templates.TemplateResponse(
                request=request,
                name="closed-down.html",
                context=context
            )

        else:
            response = await call_next(request)
            return response


class SleepMiddleware:
    """Middleware to sleep for 3 seconds in development environment
    used when developing and testing loading states"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if SETTINGS.ENVIRONMENT == "dev":
            print(
                f"development environment detecting, sleeping for {SETTINGS.SLEEP_TIME} seconds")
            time.sleep(SETTINGS.SLEEP_TIME)  # Delay for 3000ms (3 seconds)
        await self.app(scope, receive, send)


app.add_middleware(SleepMiddleware)
app.add_middleware(ClosingDownMiddleware)

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(profile_router.router)
app.include_router(shift_router.router)
app.include_router(calendar_router.router)
app.include_router(share_router.router)
app.include_router(chat_router.router)
app.include_router(scheduling_router.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

handler = Mangum(app)


@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("not-found.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user=Depends(auth_service.user_dependency)
):
    """Index page"""
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    current_month = calendar_service.get_current_month(month)
    current_year = calendar_service.get_current_year(year)

    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=current_month):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
        })

    # get previous and next month names for month navigation
    prev_month_name, next_month_name = calendar_service.get_prev_and_next_month_names(
        current_month=current_month)

    month_calendar = calendar_service.get_month_calendar(
        current_year, current_month)

    month_calendar_dict = dict((str(day), {"date": str(
        day), "day_number": day.day, "month_number": day.month, "shifts": [], "bae_shifts": []}) for day in month_calendar)

    # get unread message count so chat icon can display the count on page load
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    # get user the sent their calendar to current user if any
    bae_user = db.query(DBUser).join(DbShare, DBUser.id == DbShare.sender_id).filter(
        DbShare.receiver_id == current_user.id).first()

    if bae_user:
        if bae_user.has_birthday() and bae_user.birthday_in_current_month(current_month=current_month):
            birthdays.append({
                "name": bae_user.display_name,
                "day": bae_user.birthday.day
            })

    # gathering user ids to query shift table and get shifts for both users at once
    user_ids = [current_user.id]
    if bae_user:
        user_ids.append(bae_user.id)

    all_shifts = db.query(DbShift, DbShiftType).join(DbShiftType, DbShift.type_id == DbShiftType.id).filter(
        DbShift.user_id.in_(user_ids)).all()

    for shift, shift_type in all_shifts:
        shift_date = str(shift.date.date())
        shift.long_name = shift_type.long_name
        shift.short_name = shift_type.short_name
        if month_calendar_dict.get(shift_date):
            # find current user shifts
            if shift.user_id == current_user.id:
                month_calendar_dict[shift_date]['shifts'].append(
                    shift.__dict__)
            # find bae user shifts
            else:
                month_calendar_dict[shift_date]['bae_shifts'].append(
                    shift.__dict__)

    context = {
        "request": request,
        "birthdays": birthdays,
        "month_number": month,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "current_year": current_year,
        "current_month_number": current_month,
        "current_month": calendar_service.MONTHS[current_month - 1],
        "prev_month_name": prev_month_name,
        "next_month_name": next_month_name,
        "message_count": message_count,
        "current_user": current_user,
        "month_calendar": list(month_calendar_dict.values())
    }

    if "hx-request" in request.headers:
        response = templates.TemplateResponse(
            name="calendar/fragments/calendar-oob.html",
            context=context,
        )
    else:
        response = templates.TemplateResponse(
            name="calendar/index.html",
            context=context,
        )

    return response

@app.get("/quick-setup/first-shift", response_class=HTMLResponse)
def get_quick_setup_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    context= {
        "request": request,
        "current_user": current_user,
        "message_count": 0
    }

    return templates.TemplateResponse(name="/quick-setup/index.html", context=context)

@app.post("/quick-setup/first-shift", response_class=HTMLResponse)
def store_first_shift(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    shift_name: Annotated[str, Form()],
):
    current_time = datetime.datetime.now()
    year = current_time.year
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
        
        date_object = datetime.date(year=date[0], month=date[1], day=date[2])
        date_dict = {
            f"{year_string}-{month_string}-{day_string}": {
                "date_string": f"{date_object.year}-{month_string}-{day_string}",
                "day_of_week": str(calendar_service.Weekday(date[3])),
                "date_object": date_object
            }
        }
        if date[1] == month:
            calendar_date_list.update(date_dict)
    long_name_split = shift_name.split(" ")
    short_name = ""
    for part in long_name_split:
        short_name += part[0].upper()
    # get new shift type data ready
    new_shift_type = schemas.CreateShiftType(
        long_name=shift_name,
        short_name=short_name,
        user_id=current_user.id
    )

    # create new shift type or return an error
    shift_type_repository.create_shift_type(
        db=db,
        shift_type=new_shift_type
    )
    
    shift_types = shift_type_repository.list_user_shift_types(db=db, user_id=current_user.id)
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

    context= {
        "request": request,
        "current_user": current_user,
        "month_calendar": calendar_date_list,
        "shift_types": shift_types,
        "user_shifts": user_shifts
    }
    response = templates.TemplateResponse(
        name="/quick-setup/fragments/schedule-shift.html",                               
        context=context
        )
    response.headers["HX-Push-Url"] = "/quick-setup/schedule-shift"

    return response

@app.get("/quick-setup/schedule-shift")
def get_schedule_first_shift_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
):
    current_time = datetime.datetime.now()
    year = current_time.year
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
        
        date_object = datetime.date(year=date[0], month=date[1], day=date[2])
        date_dict = {
            f"{year_string}-{month_string}-{day_string}": {
                "date_string": f"{date_object.year}-{month_string}-{day_string}",
                "day_of_week": str(calendar_service.Weekday(date[3])),
                "date_object": date_object
            }
        }
        if date[1] == month:
            calendar_date_list.update(date_dict)
    shift_types = shift_type_repository.list_user_shift_types(db=db, user_id=current_user.id)

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
    context= {
        "request": request,
        "current_user": current_user,
        "month_calendar": calendar_date_list,
        "shift_types": shift_types,
        "user_shifts": user_shifts,
    }

    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="/quick-setup/fragments/schedule-shift.html",                               
            context=context
            )
        response.headers["HX-Push-Url"] = "/quick-setup/schedule-shift"
        return response
    
    context.update({"message_count": 0})

    response = templates.TemplateResponse(
        name="/quick-setup/scheduling.html",
        context=context
    )
    return response

@app.get("/quick-setup/username", response_class=HTMLResponse)
def get_quick_setup_page(
    request: Request,
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    context={
        "request": request,
        "current_user": current_user
        }
    
    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="/quick-setup/fragments/username.html",
            context=context
        )
        response.headers["HX-Push-Url"] = "/quick-setup/username"

        return response
    
    context.update({"message_count": 0})

    response = templates.TemplateResponse(
        name="/quick-setup/username-step.html",
        context=context
    )

    return response

# @app.post("/{date}/{type_id}", response_class=HTMLResponse)
# async def add_shift_to_date(
#     request: Request,
#     db: Annotated[Session, Depends(get_db)],
#     date: str,
#     type_id: int
# ):
#     if not auth_service.get_session_cookie(request.cookies):
#         return templates.TemplateResponse(
#             request=request,
#             name="website/web-home.html",
#             headers={"HX-Redirect": "/"},
#         )

#     current_user = auth_service.get_current_session_user(
#         db=db,
#         cookies=request.cookies)

#     # check if shift already exists
#     # if exists delete, user will already have clicked a confirm on the frontend

#     date_segments = date.split("-")
#     db_shift = schemas.CreateShift(
#         type_id=type_id,
#         user_id=current_user.id,
#         date=datetime.datetime(int(date_segments[0]), int(
#             date_segments[1]), int(date_segments[2]))
#     )

#     new_shift = shift_repository.create_shift(db=db, shift=db_shift)

#     shift_type = shift_type_repository.get_user_shift_type(
#         db=db, user_id=current_user.id, shift_type_id=type_id)

#     context = {
#         "current_user": current_user,
#         "request": request,
#         "date": {"date_string": date},
#         "shifts": [new_shift],
#         "type": shift_type
#     }

#     return templates.TemplateResponse(
#         name="/scheduling/fragments/shift-exists-button.html",
#         context=context,
#     )

@app.post("/search", response_class=HTMLResponse)
def search_users_to_share(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    search_username: Annotated[str, Form()] = "",
    current_user=Depends(auth_service.user_dependency)
):
    """ Returns a list of users that match the search string. """
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    if search_username == "":
        return templates.TemplateResponse(
            request=request,
            name="profile/search-results.html",
            context={"request": request, "matched_user": ""}
        )

    matched_user = user_repository.get_user_by_username(
        db=db,
        username=search_username
    )

    context = {
        "request": request,
        "matched_user": matched_user
    }

    return templates.TemplateResponse(
        request=request,
        name="profile/search-results.html",
        context=context
    )
