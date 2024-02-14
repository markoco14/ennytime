"""Main file to hold app and api routes"""
import datetime
from typing import Annotated, Optional

from fastapi import FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


from auth import auth_service, router as auth_router
from admin import router as admin_router
from user import router as user_router
import calendar_service
import memory_db
from repositories import shift_type_repository as ShiftTypeRepository
from schemas import Session, Shift, ShiftType, User

app = FastAPI()
app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(user_router.router)

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

    if auth_service.is_session_expired(expiry=session_data.expires_at):
        auth_service.destroy_db_session(session_token=session_data.session_id)
        response = templates.TemplateResponse(
            request=request,
            name="landing-page.html"
            )
        response.delete_cookie("session-id")
    
        return response
       
    try:
        current_user: User = auth_service.get_current_user(user_id=session_data.user_id)
    except AttributeError:
        # TODO: figure out how to specify because may be other errors
        # although this response may just be fine
        # AttributeError: 'NoneType' object has no attribute 'user_id'
        response = templates.TemplateResponse(
        request=request,
        name="signin.html",
        headers={"HX-Redirect": "/signin"},
    )
        response.delete_cookie("session-id")
        return response

    current_month = calendar_service.get_current_month(month)
    current_year = calendar_service.get_current_year(year)

    month_calendar = calendar_service.get_month_calendar(current_year, current_month)
    
    month_calendar_dict = dict((str(day), {"date": str(day), "day_number": day.day, "month_number": day.month, "shifts": [], "bae_shifts": []}) for day in month_calendar)
    
    
    shift_types = ShiftTypeRepository.list_user_shift_types(
        user_id=current_user.id)
    shift_type_dict = dict((str(shift_type.id), shift_type) for shift_type in shift_types)

    
    for shift in memory_db.SHIFTS:
        if month_calendar_dict.get(str(shift.date.date())) and shift.user_id == current_user.id:
            month_calendar_dict[str(shift.date.date())]['shift_type_id'] = shift.type_id
            month_calendar_dict[str(shift.date.date())]['shift_type'] = shift_type_dict.get(str(shift.type_id))
            month_calendar_dict[str(shift.date.date())]['shifts'].append(shift)

    # handle shared shifts
    shares = list(memory_db.SHARES.values())
    shared_with_me = []
    for share in shares:
        if share.guest_id == current_user.id:
            shared_with_me.append(share)
    if len(shared_with_me) >= 1:
        bae_calendar = shared_with_me[0] # a user can only share with 1 person for now
        # but could get list of just bae.owner_id and loop through that
        # adding shifts to the 'shared with me' section of calendar card
        
        for shift in memory_db.SHIFTS:
            if month_calendar_dict.get(str(shift.date.date())) and shift.user_id == bae_calendar.owner_id:
                month_calendar_dict[str(shift.date.date())]['bae_shifts'].append(shift)
        

    context = {
        "request": request,
        "days_of_week": calendar_service.DAYS_OF_WEEK,
        "current_year": current_year,
        "current_month_number": current_month,
        "current_month": calendar_service.MONTHS[current_month - 1],
        "month_calendar": list(month_calendar_dict.values()),
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

    date_string = datetime.datetime(
        current_year,
        current_month,
        day_number
        ).date()

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


@app.get("/calendar-card/{date_string}", response_class=HTMLResponse)
def get_calendar_day_card(request: Request, date_string: str):
    """Get calendar day card"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )
    
    session_data: Session = auth_service.get_session_data(request.cookies.get("session-id"))

    current_user: User = auth_service.get_current_user(user_id=session_data.user_id)
    date_segments = date_string.split("-")

    shifts = []
    for shift in memory_db.SHIFTS:
        if str(shift.date.date()) == date_string and shift.user_id == current_user.id:
            shift.type = ShiftTypeRepository.get_shift_type(shift_type_id=shift.type_id)
            shifts.append(shift)


    # handle shared shifts
    shares = list(memory_db.SHARES.values())
    shared_with_me = []
    for share in shares:
        if share.guest_id == current_user.id:
            shared_with_me.append(share)
    if len(shared_with_me) >= 1:
        bae_calendar = shared_with_me[0] # a user can only share with 1 person for now
        # but could get list of just bae.owner_id and loop through that
        # adding shifts to the 'shared with me' section of calendar card
        bae_shifts = []
        for shift in memory_db.SHIFTS:
            if str(shift.date.date()) == date_string and shift.user_id == bae_calendar.owner_id:
                bae_shifts.append(shift)

    context = {
        "request": request,
        "date_string": date_string,
        "date": {
            "shifts": shifts,
            "day_number": int(date_segments[2]),
            "bae_shifts": bae_shifts,
            },
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
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )
    
    session_data: Session = auth_service.get_session_data(request.cookies.get("session-id"))

    current_user: User = auth_service.get_current_user(user_id=session_data.user_id)
  
    date_segments = date.split("-")
    new_shift = Shift(
        id=len(memory_db.SHIFTS) + 1,
        type_id=shift_type,
        user_id=current_user.id,
        date=datetime.datetime(int(date_segments[0]), int(date_segments[1]), int(date_segments[2]))
        )
    
    # REMOVED CHECK FOR SHIFT EXISTS/DAY HAS SHIFT
    # TODO: check if day already has that shift type
    # a day might have 2 shifts (for now, because might have 2 jobs)
    memory_db.SHIFTS.append(new_shift)

    context={"request": request,
        "shifts": memory_db.SHIFTS,
          }
    
    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context=context
    )

@app.post("/search", response_class=HTMLResponse)
def search_users_to_share(
    request: Request,
    search_display_name: Annotated[str, Form()] = ""
    ):
    """ Returns a list of users that match the search string. """
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html"
        )

    session_data: Session = auth_service.get_session_data(request.cookies.get("session-id"))

    if auth_service.is_session_expired(expiry=session_data.expires_at):
        auth_service.destroy_db_session(session_token=session_data.session_id)
        response = templates.TemplateResponse(
            request=request,
            name="landing-page.html"
            )
        response.delete_cookie("session-id")
    
        return response
       
    try:
        current_user: User = auth_service.get_current_user(user_id=session_data.user_id)
    except AttributeError:
        # TODO: figure out how to specify because may be other errors
        # although this response may just be fine
        # AttributeError: 'NoneType' object has no attribute 'user_id'
        response = templates.TemplateResponse(
        request=request,
        name="signin.html",
        headers={"HX-Redirect": "/signin"},
    )
        response.delete_cookie("session-id")
        return response
    
    if search_display_name == "":
        return templates.TemplateResponse(
            request=request,
            name="search-results.html",
            context={"request": request, "matching_users": []}
        )
    
    search_display_name_lower = search_display_name.lower()
    user_list = list(memory_db.USERS.values())
    matching_users = []
    for user in user_list:
        if user.display_name and search_display_name_lower in user.display_name.lower() and user.id != current_user.id:
           matching_users.append(user)
        
    context = {"request": request, "matching_users": matching_users}

    return templates.TemplateResponse(
        request=request,
        name="search-results.html",
        context=context
    )

