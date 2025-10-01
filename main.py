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

from router import router as app_router

from app.auth import auth_router, auth_service
from app.core.database import get_db
from app.core.config import get_settings
from app.core.template_utils import templates
from app.repositories import user_repository
from app.routers import (
    admin_router,
    calendar_router,
    share_router,
    chat_router,
    onboard_router
)


SETTINGS = get_settings()


app = FastAPI()

app.include_router(app_router)

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
        


class MaintenanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(
            self,
            request: Request,
            call_next: RequestResponseEndpoint
    ):
        if SETTINGS.MAINTENANCE_MODE == "true":
            logging.info("Maintenance Mode is on")
            # Allow `/maintenance` to bypass the maintenance check
            if request.url.path == "/maintenance":
                logging.info("direct access to maintenance page, allowing")
                return await call_next(request)
            
            if request.headers.get("HX-Request"):      
                logging.info("attempted hx-request access to resource, redirecting to maintenance page")
                response = templates.TemplateResponse(
                    "maintenance.html",
                    {"request": request}
                )
                response.headers["HX-Redirect"] = "/maintenance"
                return response
            
            logging.info("attempted non-hx access to resource, redirecting to maintenance page")
            return RedirectResponse(url="/maintenance")
        else:
            logging.info("Maintenance Mode is off")
            if request.url.path == "/maintenance":
                logging.info("attempted access to maintenance page, redirecting to home")
                return RedirectResponse(url="/")
            
            logging.info("attempted access to resource, allowing")
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
app.add_middleware(MaintenanceMiddleware)

app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(calendar_router.router)
app.include_router(share_router.router)
app.include_router(chat_router.router)
app.include_router(onboard_router.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

handler = Mangum(app)



@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("not-found.html", {"request": request})


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

@app.get("/maintenance", response_class=HTMLResponse)
def maintenance_page(request: Request):
    """Maintenance page"""
    return templates.TemplateResponse(
        request=request,
        name="maintenance.html"
    )