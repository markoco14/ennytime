"""Main file to hold app and api routes"""

from typing import Annotated
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


from auth import router as auth_router
import time_service

app = FastAPI()
app.include_router(auth_router.router)

templates = Jinja2Templates(directory="templates")


class ScheduleDay(BaseModel):
    """Schedule day"""
    date: int
    type: str



DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

SHIFT_TYPES = []

SHIFTS = []



MONTH_CALENDAR = time_service.get_month_calendar(2024, 2)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, response: Response):
    """Index page"""

    if not request.cookies.get("session-test"):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html"
        )
    context = {
        "request": request,
        "days_of_week": DAYS_OF_WEEK,
        "month_calendar": MONTH_CALENDAR,
        "shifts": SHIFTS,
    }

    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
        )
    
    return response


@app.get("/signin", response_class=HTMLResponse)
def get_signin_page(request: Request, response: Response):
    """Go to the sign in page"""
    return templates.TemplateResponse(
        request=request,
        name="signin.html",
        )


@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    """Profile page"""
    context = {
        "request": request,
        "shift_types": SHIFT_TYPES,
    }

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context=context
        )


@app.post("/register-shift-type", response_class=HTMLResponse)
def register_shift_type(request: Request, shift_type: Annotated[str, Form()]):
    """Register shift type"""
    SHIFT_TYPES.append(shift_type)
    context={
        "request": request,
        "shift_types": SHIFT_TYPES,
          }

    return templates.TemplateResponse(
        request=request,
        name="shifts/shift-list.html", # change to list template
        context=context
    )


@app.get("/add-shift-form/{day_number}", response_class=HTMLResponse)
def get_calendar_day_form(request: Request, day_number: int):
    """Get calendar day form"""

    context={
        "request": request,
        "shift_types": SHIFT_TYPES,
        "day_number": day_number,
          }

    return templates.TemplateResponse(
        request=request,
        name="/calendar/add-shift-form.html",
        context=context
        )


@app.get("/calendar-card/{day_number}", response_class=HTMLResponse)
def get_calendar_day_card(request: Request, day_number: int):
    """Get calendar day card"""
    context = {
        "request": request,
        "day_number": day_number,
        "shifts": SHIFTS,    
    }

    return templates.TemplateResponse(
        request=request,
        name="/calendar/calendar-day-card.html",
        context=context,
    )


@app.get("/modal/{day_number}", response_class=HTMLResponse)
def modal(request: Request, day_number: int):
    """Sends modal to client"""

    context={
        "request": request,
        "shift_types": SHIFT_TYPES,
        "day_number": day_number,
          }

    return templates.TemplateResponse(
        request=request,
        name="modal.html",
        context=context
        )


@app.post("/register-shift", response_class=HTMLResponse)
def schedule_shift(
    request: Request,
    shift_type: Annotated[str, Form()],
    date: Annotated[int, Form()],
    ):
    """Add shift to calendar date"""
    new_shift = ScheduleDay(date=date, type=shift_type)
    shift_types = SHIFT_TYPES
    if new_shift in SHIFTS:
        context={"request": request,
            "days_of_week": DAYS_OF_WEEK,
            "month_calendar": MONTH_CALENDAR,
            "shifts": SHIFTS,
            "shift_types": shift_types,
            "day_number": date,
            }
        return templates.TemplateResponse(
            request=request,
            name="shift-exists.html",
            context=context
        )
    SHIFTS.append(new_shift)

    context={"request": request,
        "days_of_week": DAYS_OF_WEEK,
        "month_calendar": MONTH_CALENDAR,
        "shifts": SHIFTS,
          }
    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context=context
    )