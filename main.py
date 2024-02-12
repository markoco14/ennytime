"""Main file to hold app and api routes"""
from typing import Annotated, Optional

from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


from auth import auth_service, router as auth_router
import calendar_service
import memory_db
from repositories import shift_type_repository as ShiftTypeRepository
from repositories import user_repository as UserRepository
from repositories import session_repository as SessionRepository
from schemas import ScheduleDay, Session, ShiftType, User

app = FastAPI()
app.include_router(auth_router.router)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    response: Response,
    month: Optional[int] = None,
    year: Optional[int] = None,
    ):
    """Index page"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html"
        )

    current_month = calendar_service.get_current_month(month)
    current_year = calendar_service.get_current_year(year)

    month_calendar = calendar_service.get_month_calendar(current_year, current_month)

    context = {
        "request": request,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "current_year": current_year,
        "current_month": calendar_service.MONTHS[current_month - 1],
        "month_calendar": month_calendar,
        "shifts": memory_db.SHIFTS,
    }

    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context=context
        )
    
    return response


@app.get("/signin", response_class=HTMLResponse)
def get_signin_page(request: Request):
    """Go to the sign in page"""
    return templates.TemplateResponse(
        request=request,
        name="signin.html",
        )


@app.get("/profile", response_class=HTMLResponse | Response)
def profile(request: Request):
    """Profile page"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: Session = auth_service.get_session_data(request.cookies.get("session-id"))
    
    current_user: User = auth_service.get_current_user(user_id=session_data.user_id)

    shift_types = ShiftTypeRepository.list_user_shift_types(
        user_id=current_user.id)
    
    context = {
        "request": request,
        "shift_types": shift_types,
        "user": current_user,
    }

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context=context
        )

@app.get("/users", response_class=HTMLResponse)
def list_users(request: Request):
    """List users"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )
    
    users = UserRepository.list_users()
    context = {
        "request": request,
        "users": users,
    }
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context=context
    )
@app.get("/sessions", response_class=HTMLResponse)
def list_sessions(request: Request):
    """List sessions"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )
    
    sessions = SessionRepository.list_sessions()
    context = {
        "request": request,
    "sessions": sessions,
    }
    return templates.TemplateResponse(
        request=request,
        name="sessions.html",
        context=context
    )

@app.post("/register-shift-type", response_class=HTMLResponse)
def register_shift_type(request: Request, shift_type: Annotated[str, Form()]):
    """Register shift type"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )
    
    session_data: Session = auth_service.get_session_data(request.cookies.get("session-id"))

    current_user: User = auth_service.get_current_user(user_id=session_data.user_id)
            
    new_shift_type = ShiftType(
        id=len(memory_db.SHIFT_TYPES) + 1,
        type=shift_type,
        user_id=current_user.id
    )
    memory_db.SHIFT_TYPES.append(new_shift_type)

    shift_types = [shift_type for shift_type in memory_db.SHIFT_TYPES if shift_type.user_id == current_user.id]
    context={
        "request": request,
        "shift_types": shift_types,
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
        "shift_types": memory_db.SHIFT_TYPES,
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
        "shifts": memory_db.SHIFTS,    
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
        "shift_types": memory_db.SHIFT_TYPES,
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
    shift_types = memory_db.SHIFT_TYPES
    if new_shift in memory_db.SHIFTS:
        context={"request": request,
            "days_of_week": calendar_service.DAYS_OF_WEEK,
            # "month_calendar": MONTH_CALENDAR,
            "shifts": memory_db.SHIFTS,
            "shift_types": shift_types,
            "day_number": date,
            }
        return templates.TemplateResponse(
            request=request,
            name="shift-exists.html",
            context=context
        )
    memory_db.SHIFTS.append(new_shift)

    context={"request": request,
        # "days_of_week": DAYS_OF_WEEK,
        # "month_calendar": MONTH_CALENDAR,
        "shifts": memory_db.SHIFTS,
          }
    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context=context
    )