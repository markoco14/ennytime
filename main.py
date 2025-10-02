"""Main file to hold app and api routes"""
import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from mangum import Mangum
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint

from router import router as app_router

from app.auth import auth_router
from app.core.config import get_settings
from app.core.template_utils import templates
from app.routers import (
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
app.include_router(chat_router.router)
app.include_router(onboard_router.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

handler = Mangum(app)



@app.exception_handler(404)
async def custom_404_handler(request, __):
    return templates.TemplateResponse("not-found.html", {"request": request})



@app.get("/maintenance", response_class=HTMLResponse)
def maintenance_page(request: Request):
    """Maintenance page"""
    return templates.TemplateResponse(
        request=request,
        name="maintenance.html"
    )