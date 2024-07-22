"""Main file to hold app and api routes"""
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
from app.core.template_utils import templates, block_templates
from app.repositories import share_repository, shift_repository
from app.repositories import user_repository
from app.routers import admin_router, calendar_router, share_router, shift_router, shift_type_router, user_router, chat_router
from app.services import calendar_service, chat_service

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
app.include_router(user_router.router)
app.include_router(shift_type_router.router)
app.include_router(shift_router.router)
app.include_router(calendar_router.router)
app.include_router(share_router.router)
app.include_router(chat_router.router)

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
):
    """Index page"""
    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    if not month:
        current_month = calendar_service.get_current_month(month)
    else:
        current_month = month

    birthdays = []
    if current_user.__dict__["birthday"] and month == current_user.__dict__["birthday"].month:
        birthdays.append({
            "name": current_user.display_name,
            "day": current_user.__dict__["birthday"].day
        })

    if not year:
        current_year = calendar_service.get_current_year(year)
    else:
        current_year = year

    if current_month == 1:
        prev_month_name = calendar_service.MONTHS[11]
    else:
        prev_month_name = calendar_service.MONTHS[current_month - 2]

    if current_month == 12:
        next_month_name = calendar_service.MONTHS[0]
    else:
        next_month_name = calendar_service.MONTHS[current_month]

    month_calendar = calendar_service.get_month_calendar(
        current_year, current_month)

    month_calendar_dict = dict((str(day), {"date": str(
        day), "day_number": day.day, "month_number": day.month, "shifts": [], "bae_shifts": []}) for day in month_calendar)

    if current_user.display_name is not None:
        display_name = current_user.display_name.split(" ")[0]
    else:
        display_name = "NewUser00001"

    user_page_data = {
        "display_name": display_name,
        "is_admin": current_user.is_admin
    }

    # get unread message count so chat icon can display the count on page load
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    

    # TODO: add month filters to shift query
    # because right now we get all the shifts in the db belonging to the user
    db_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=current_user.id)
    for shift in db_shifts:
        shift_date = str(shift.date.date())
        if month_calendar_dict.get(shift_date):
            month_calendar_dict[shift_date]['shifts'].append(shift._asdict())

    # check if any other users have shared their calendars with the current user
    # so we can get that calendar data and show on the screen
    shared_with_me = share_repository.get_share_from_other_user(
        db=db, guest_id=current_user.id)

    if not shared_with_me:
        context.update(month_calendar=list(month_calendar_dict.values()))
        response = templates.TemplateResponse(
            request=request,
            name="app-home.html",
            context=context,
        )

        return response

    # ... ok let's get the share first
    bae_user = share_repository.get_share_user_with_shifts_by_guest_id(
        db=db, share_user_id=shared_with_me.owner_id)

    if bae_user.birthday and month == bae_user.birthday.month:
        birthdays.append({
            "name": bae_user.display_name,
            "day": bae_user.birthday.day
        })

    bae_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=shared_with_me.owner_id)
    for shift in bae_shifts:
        shift_date = str(shift.date.date())
        if month_calendar_dict.get(shift_date):
            month_calendar_dict[shift_date]['bae_shifts'].append(
                shift._asdict())
            
    context = {
        "request": request,
        "birthdays": birthdays,
        "user_data": user_page_data,
        "month_number": month,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "current_year": current_year,
        "current_month_number": current_month,
        "current_month": calendar_service.MONTHS[current_month - 1],
        "prev_month_name": prev_month_name,
        "next_month_name": next_month_name,
        "message_count": message_count,
        "current_user": current_user.display_name,
        "bae_user": bae_user.display_name,
    }

    context.update(month_calendar=list(month_calendar_dict.values()))

    if "hx-request" in request.headers:
        response = block_templates.TemplateResponse(
            name="app-home.html",
            block_name="calendar",
            context=context,
        )
    else:
        response = templates.TemplateResponse(
            name="app-home.html",
            context=context,
        )

    return response


@app.get("/signin", response_class=HTMLResponse)
def get_signin_page(request: Request):
    """Go to the sign in page"""
    return templates.TemplateResponse(
        request=request,
        name="website/signin.html",
    )


@app.get("/signup", response_class=HTMLResponse)
def get_signup_page(request: Request):
    """Go to the sign up page"""
    return templates.TemplateResponse(
        request=request,
        name="website/signup.html",
    )


@app.post("/search", response_class=HTMLResponse)
def search_users_to_share(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    search_display_name: Annotated[str, Form()] = ""
):
    """ Returns a list of users that match the search string. """
    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    if search_display_name == "":
        return templates.TemplateResponse(
            request=request,
            name="webapp/profile/search-results.html",
            context={"request": request, "matching_users": []}
        )

    search_display_name_lower = search_display_name.lower()

    matching_users = user_repository.list_users_by_display_name(
        db=db, current_user_id=current_user.id, display_name=search_display_name_lower)

    context = {"request": request, "matching_users": matching_users}

    return templates.TemplateResponse(
        request=request,
        name="webapp/profile/search-results.html",
        context=context
    )

# @app.get("/development")
# def get_development_page(request: Request):
#     return templates.TemplateResponse(
#         request=request,
#         name="development.html",
#     )
