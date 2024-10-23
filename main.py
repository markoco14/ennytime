"""Main file to hold app and api routes"""
import datetime
from typing import Annotated, Optional
from pprint import pprint
import time
from fastapi import Depends, FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from mangum import Mangum
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from app.auth import auth_router, auth_service
from app.core.database import get_db
from app.core.config import get_settings
from app.core.template_utils import templates
from app.repositories import user_repository
from app.routers import (
    admin_router,
    calendar_router,
    profile_router,
    share_router,
    shift_router,
    chat_router,
    scheduling_router,
    onboard_router
)
from app.services import calendar_service, calendar_shift_service, chat_service
from app.models.user_model import DBUser
from app.models.share_model import DbShare



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
app.include_router(onboard_router.router)

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
    current_time = datetime.datetime.now()
    selected_year = year or current_time.year
    selected_month = month or current_time.month
    selected_month_name = calendar_service.MONTHS[selected_month - 1]

    birthdays = []
    if current_user.has_birthday() and current_user.birthday_in_current_month(current_month=selected_month):
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.birthday.day
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

    # get unread message count so chat icon can display the count on page load
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    # get user the sent their calendar to current user if any
    bae_user = db.query(DBUser).join(DbShare, DBUser.id == DbShare.sender_id).filter(
        DbShare.receiver_id == current_user.id).first()

    if bae_user:
        if bae_user.has_birthday() and bae_user.birthday_in_current_month(current_month=selected_month):
            birthdays.append({
                "name": bae_user.display_name,
                "day": bae_user.birthday.day
            })

    # gathering user ids to query shift table and get shifts for both users at once
    user_ids = [current_user.id]
    if bae_user:
        user_ids.append(bae_user.id)

    # get shifts for current user and bae user
    all_shifts = calendar_shift_service.get_shift_info_for_users(db=db, user_ids=user_ids)
    
    # update the calendar dictionary with sorted shifts
    month_calendar_dict = calendar_shift_service.sort_shifts_by_user(all_shifts=all_shifts, month_calendar_dict=month_calendar_dict, current_user=current_user)

    context = {
        "request": request,
        "current_user": current_user,
        "birthdays": birthdays,
        "selected_month": selected_month,
        "selected_month_name": selected_month_name,
        "selected_year": selected_year,
        "prev_month_name": prev_month_name,
        "next_month_name": next_month_name,
        "month_calendar": list(month_calendar_dict.values()),
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "message_count": message_count,
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
