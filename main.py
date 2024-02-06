"""Main file to hold app and api routes"""

from typing import Annotated
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


import time_service

app = FastAPI()

templates = Jinja2Templates(directory="templates")

class ScheduleDay(BaseModel):
    """Schedule day"""
    date: int
    type: str

DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

SHIFT_TYPES = ['Night']

SHIFTS = []

MONTH_CALENDAR = time_service.get_month_calendar(2024, 2)
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Index page"""

    context = {
        "request": request,
        "days_of_week": DAYS_OF_WEEK,
        "month_calendar": MONTH_CALENDAR,
        "shifts": SHIFTS,
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
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