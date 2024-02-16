
from typing import Annotated, Optional
import datetime
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.exc import IntegrityError

from auth import auth_service
from core.database import get_db
import core.memory_db as memory_db

from schemas import CreateShift, Session, Shift, User
import schemas
from repositories import shift_repository, shift_type_repository
from services import calendar_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/add-shift-form/{day_number}", response_class=HTMLResponse)
def get_calendar_day_form(
    request: Request,
    day_number: int,
    db: Annotated[Session, Depends(get_db)],
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
    
    session_data: Session = auth_service.get_session_data(db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.AppUser = auth_service.get_current_user(db=db, user_id=session_data.user_id)

    shift_types = shift_type_repository.list_user_shift_types(
        db=db,
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




@router.get("/calendar-card/{date_string}", response_class=HTMLResponse)
def get_calendar_day_card(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    date_string: str):
    """Get calendar day card"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )
    
    session_data: Session = auth_service.get_session_data(db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.AppUser = auth_service.get_current_user(db=db, user_id=session_data.user_id)
    date_segments = date_string.split("-")
    db_shifts = shift_repository.get_user_shifts(db=db, user_id=current_user.id)
    shifts = []
    for shift in db_shifts:
        if str(shift.date.date()) == date_string and shift.user_id == current_user.id:
            # shift.type = shift_type_repository.get_user_shift_type(shift_type_id=shift.type_id)
            db_shift_type = shift_type_repository.get_user_shift_type(db=db, user_id=current_user.id, shift_type_id=shift.type_id)
            shifts.append(db_shift_type)


    # handle shared shifts
    shares = list(memory_db.SHARES.values())
    shared_with_me = []
    for share in shares:
        if share.guest_id == current_user.id:
            shared_with_me.append(share)
    bae_shifts = []
    if len(shared_with_me) >= 1:
        bae_calendar = shared_with_me[0] # a user can only share with 1 person for now
        # but could get list of just bae.owner_id and loop through that
        # adding shifts to the 'shared with me' section of calendar card
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