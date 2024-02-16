"""Main file to hold app and api routes"""
import datetime
from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Request, Form, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from pprint import pprint
from auth import auth_router, auth_service
from core.database import get_db
from routers import admin_router, user_router, shift_type_router, shift_router, calendar_router
from services import calendar_service
import core.memory_db as memory_db
from repositories import shift_type_repository, shift_repository, user_repository
from schemas import Session, Shift, ShiftType, User, AppUser

app = FastAPI()
app.include_router(auth_router.router)
app.include_router(admin_router.router)
app.include_router(user_router.router)
app.include_router(shift_type_router.router)
app.include_router(shift_router.router)
app.include_router(calendar_router.router)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    month: Optional[int] = None,
    year: Optional[int] = None,
    ):
    """Index page"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html"
        )
    try:
        session_data: Session = auth_service.get_session_data(db=db, session_token=request.cookies.get("session-id"))
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
    
    if auth_service.is_session_expired(expiry=session_data.expires_at):
        auth_service.destroy_db_session(db=db, session_token=session_data.session_id)
        response = templates.TemplateResponse(
            request=request,
            name="landing-page.html"
            )
        response.delete_cookie("session-id")
    
        return response
       
    try:
        current_user: AppUser = auth_service.get_current_user(db=db, user_id=session_data.user_id)
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
    
    
    # shift_types = shift_type_repository.list_user_shift_types(
    #     db=db,
    #     user_id=current_user.id)
    # shift_type_dict = dict((str(shift_type.id), shift_type) for shift_type in shift_types)

    db_shifts = shift_repository.get_user_shifts(db=db, user_id=current_user.id)
    
    # get users detailed shift info for matching dates
    for shift in db_shifts:
        shift_date = str(shift.date.date())
        if month_calendar_dict.get(shift_date):
            db_shift_type = shift_type_repository.get_user_shift_type(db=db, user_id=current_user.id, shift_type_id=shift.type_id)
            # month_calendar_dict[shift_date]['shift_type_id'] = shift.type_id
            # month_calendar_dict[shift_date]['shift_type'] = db_shift_type
            month_calendar_dict[shift_date]['shifts'].append(db_shift_type)
        

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


# @app.get("/modal/{day_number}", response_class=HTMLResponse)
# def modal(request: Request, day_number: int):
#     """Sends modal to client"""

#     context={
#         "request": request,
#         "shift_types": memory_db.SHIFT_TYPES,
#         "day_number": day_number,
#           }

#     return templates.TemplateResponse(
#         request=request,
#         name="modal.html",
#         context=context
#         )


@app.post("/search", response_class=HTMLResponse)
def search_users_to_share(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    search_display_name: Annotated[str, Form()] = ""
    ):
    """ Returns a list of users that match the search string. """
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html"
        )

    session_data: Session = auth_service.get_session_data(db=db, session_token=request.cookies.get("session-id"))

    if auth_service.is_session_expired(expiry=session_data.expires_at):
        auth_service.destroy_db_session(db=db, session_token=session_data.session_id)
        response = templates.TemplateResponse(
            request=request,
            name="landing-page.html"
            )
        response.delete_cookie("session-id")
    
        return response
       
    try:
        current_user: User = auth_service.get_current_user(db=db, user_id=session_data.user_id)
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

    matching_users = user_repository.list_users_by_display_name(db=db, current_user_id=current_user.id, display_name=search_display_name_lower)
        
    context = {"request": request, "matching_users": matching_users}

    return templates.TemplateResponse(
        request=request,
        name="search-results.html",
        context=context
    )

