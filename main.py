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

    session_data: Session = auth_service.get_session_data(request.cookies.get("session-id"))
    
    current_user: User = auth_service.get_current_user(user_id=session_data.user_id)

    current_month = calendar_service.get_current_month(month)
    current_year = calendar_service.get_current_year(year)

    month_calendar = calendar_service.get_month_calendar(current_year, current_month)
    
    month_dictionary = dict((str(day), {"date": str(day)}) for day in month_calendar)
    
    
    shift_types = ShiftTypeRepository.list_user_shift_types(
        user_id=current_user.id)
    shift_type_dict = dict((str(shift_type.id), shift_type) for shift_type in shift_types)

    for shift in memory_db.SHIFTS:
        if month_dictionary.get(str(shift.date.date())):
            month_dictionary[str(shift.date.date())]['shift_type_id'] = shift.type_id
            month_dictionary[str(shift.date.date())]['shift_type'] = shift_type_dict.get(str(shift.type_id))

    context = {
        "request": request,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "current_year": current_year,
        "current_month": calendar_service.MONTHS[current_month - 1],
        "month_calendar": list(month_dictionary.values()),
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
    memory_db.SHIFT_TYPES.update({new_shift_type.id:new_shift_type})

    shift_types = ShiftTypeRepository.list_user_shift_types(
        user_id=current_user.id)
    
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
def get_calendar_day_form(
    request: Request, 
    day_number: int, 
    month: Optional[int] = None, 
    year: Optional[int] = None
    ):
    """Get calendar day form"""
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
    current_month = calendar_service.get_current_month(month)
    current_year = calendar_service.get_current_year(year)

    if day_number < 10:
        current_day = f"0{day_number}"
    else:
        current_day = day_number

    if current_month < 10:
        current_month = f"0{current_month}"
        
    date_string = f"{current_year}-{current_month}-{current_day}"
    context={
        "request": request,
        "shift_types": shift_types,
        "day_number": day_number,
        "current_month": current_month,
        "current_year": current_year,
        "date_string": date_string
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
    date: Annotated[str, Form()],
    ):
    """Add shift to calendar date"""
    return templates.TemplateResponse(
        request=request,
        name="shift-exists.html",
        # context=context
    )
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