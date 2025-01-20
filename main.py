"""Main file to hold app and api routes"""
import datetime
import logging
from typing import Annotated, Optional
import time

from fastapi import Depends, FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
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


SETTINGS = get_settings()


app = FastAPI()

logging.basicConfig(
    level=logging.INFO,  # Ensure INFO level messages are captured
    format="%(asctime)s - %(levelname)s - %(message)s"
)

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
# app.include_router(chat_router.router)
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
    
    # HX-Redirect required for hx-request
    if "hx-request" in request.headers:
        response = Response(status_code=303)
        response.headers["HX-Redirect"] = f"/calendar/{selected_year}/{selected_month}"
        return response
    
    # Can use FastAPI Redirect with standard http request
    return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")


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
