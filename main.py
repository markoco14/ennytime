"""Main file to hold app and api routes"""
from typing import Annotated, Optional

import time
from fastapi import Depends, FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from mangum import Mangum
from sqlalchemy.orm import Session


from app.auth import auth_router, auth_service
from app.core.database import get_db
from app.core.config import get_settings
from app.repositories import share_repository, shift_repository
from app.repositories import user_repository
from app.routers import admin_router, calendar_router, share_router, shift_router, shift_type_router, user_router, chat_router
from app.services import calendar_service, chat_service

SETTINGS = get_settings()


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


app = FastAPI()

app.add_middleware(SleepMiddleware)


app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(user_router.router)
app.include_router(shift_type_router.router)
app.include_router(shift_router.router)
app.include_router(calendar_router.router)
app.include_router(share_router.router)
app.include_router(chat_router.router)

templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")

handler = Mangum(app)
app.mount("/static", StaticFiles(directory="static"), name="static")


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

    context = {
        "request": request,
        "user_data": user_page_data,
        "month_number": month,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "current_year": current_year,
        "current_month_number": current_month,
        "current_month": calendar_service.MONTHS[current_month - 1],
        "prev_month_name": prev_month_name,
        "next_month_name": next_month_name,
        "message_count": message_count
    }

    # TODO: add month filters to shift query
    # because right now we get all the shifts in the db belonging to the user
    db_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=current_user.id)
    for shift in db_shifts:
        shift_date = str(shift.date.date())
        if month_calendar_dict.get(shift_date):
            month_calendar_dict[shift_date]['shifts'].append(shift._asdict())

    # TODO: improve 'share' naming to better reflect purpose
    # we are checking to see if anyone has shared their calendar with the current user
    share = share_repository.get_share_by_guest_id(
        db=db, guest_id=current_user.id)
    if not share:
        context.update(month_calendar=list(month_calendar_dict.values()))
        response = templates.TemplateResponse(
            request=request,
            name="webapp/home/app-home.html",
            context=context,
        )

        return response

    bae_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=share.owner_id)
    for shift in bae_shifts:
        shift_date = str(shift.date.date())
        if month_calendar_dict.get(shift_date):
            month_calendar_dict[shift_date]['bae_shifts'].append(
                shift._asdict())

    context.update(month_calendar=list(month_calendar_dict.values()))

    if "hx-request" in request.headers:
        response = block_templates.TemplateResponse(
            name="webapp/home/app-home.html",
            block_name="calendar",
            context=context,
        )
    else:
        response = templates.TemplateResponse(
            name="webapp/home/app-home.html",
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
