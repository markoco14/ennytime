"""Main file to hold app and api routes"""

from typing import Annotated, List
from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from passlib.context import CryptContext


import time_service

app = FastAPI()

templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)
class ScheduleDay(BaseModel):
    """Schedule day"""
    date: int
    type: str

class User(BaseModel):
    """User"""
    email: str
    password: str

DAYS_OF_WEEK = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

SHIFT_TYPES = []

SHIFTS = []

USERS: List[User] = []

MONTH_CALENDAR = time_service.get_month_calendar(2024, 2)

@app.post("/signup", response_class=Response)
def signup(
    request: Request,
    response: Response,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()]
    ):
    """Sign up a user"""
    # TODO: Check if email is already in use

    # TODO: return response about email/password combo being no good
    
    # Hash password
    hashed_password = get_password_hash(password)
    
    # create new user with encrypted password
    user = User(email=email, password=hashed_password)
    
    # add user to USERS
    USERS.append(user)

    # return response with session cookie and redirect to index
    response = Response(status_code=200)
    response.set_cookie(
        key="session-test",
        value="this-is-a-session-id",
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    response.headers["HX-Redirect"] = "/"
    
    return response

@app.post("/signin", response_class=Response)
def signin(request: Request, response: Response):
    """Sign in a user"""
    response = Response(status_code=200)
    response.set_cookie(
        key="session-test",
        value="this-is-a-session-id",
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    response.headers["HX-Redirect"] = "/"
    return response


@app.get("/signout", response_class=HTMLResponse)
def signout(request: Request, response: Response):
    """Sign out a user"""
    response = Response(status_code=200)
    response.delete_cookie(key="session-test")
    response.headers["HX-Redirect"] = "/"
    return response


@app.get("/", response_class=HTMLResponse)
def index(request: Request, response: Response):
    """Index page"""

    print(request.cookies)
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


@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request):
    """Profile page"""
    print(request.cookies)
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