
from typing import Annotated, Optional
import datetime

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.auth import auth_service
from app.core.database import get_db
from app.schemas import schemas
from app.repositories import share_repository, shift_repository
from app.repositories import shift_type_repository
from app.services import calendar_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/calendar-card-detail/{date_string}", response_class=HTMLResponse)
def get_calendar_card_detailed(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    date_string: str):
    """Get calendar day card"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )
    
    session_data: schemas.Session = auth_service.get_session_data(db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.AppUser = auth_service.get_current_user(db=db, user_id=session_data.user_id)
    date_segments = date_string.split("-")
    
    db_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=current_user.id)
    
    # only need to get an array of shifts
    # becauase only for one day, not getting whole calendar
    shifts = []
    for shift in db_shifts:
        if str(shift.date.date()) == date_string:
            shifts.append(shift._asdict())

    bae_shifts = []
    share = share_repository.get_share_by_guest_id(db=db, guest_id=current_user.id)
    if share:
        bae_db_shifts = shift_repository.get_user_shifts_details(db=db, user_id=share.owner_id)
        for shift in bae_db_shifts:
            if str(shift.date.date()) == date_string:
                bae_shifts.append(shift)

    context = {
        "request": request,
        "date": {
            "date": date_string,
            "shifts": shifts,
            "day_number": int(date_segments[2]),
            "bae_shifts": bae_shifts,
            },
    }

    return templates.TemplateResponse(
        request=request,
        name="/webapp/home/calendar-card-detail.html",
        context=context,
    )


@router.get("/add-shift-form/{date_string}", response_class=HTMLResponse)
def get_calendar_day_form(
    request: Request,
    date_string: str,
    db: Annotated[Session, Depends(get_db)],
    month: Optional[int] = None,
    year: Optional[int] = None
    ):
    """Get calendar day form"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )
    
    session_data: schemas.Session = auth_service.get_session_data(db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.AppUser = auth_service.get_current_user(db=db, user_id=session_data.user_id)

    shift_types = shift_type_repository.list_user_shift_types(
        db=db,
        user_id=current_user.id)
    current_month = calendar_service.get_current_month(month)
    current_year = calendar_service.get_current_year(year)


    context={
        "request": request,
        "shift_types": shift_types,
        "day_number": int(date_string.split("-")[2]),
        "current_month": current_month,
        "current_year": current_year,
        "date_string": date_string
          }

    return templates.TemplateResponse(
        request=request,
        name="/webapp/home/add-shift-form.html",
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
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )
    
    session_data: schemas.Session = auth_service.get_session_data(db=db, session_token=request.cookies.get("session-id"))

    current_user: schemas.AppUser = auth_service.get_current_user(db=db, user_id=session_data.user_id)
    date_segments = date_string.split("-")
    
    db_shifts = shift_repository.get_user_shifts_details(
        db=db, user_id=current_user.id)
    
    # only need to get an array of shifts
    # becauase only for one day, not getting whole calendar
    shifts = []
    for shift in db_shifts:
        if str(shift.date.date()) == date_string:
            shifts.append(shift._asdict())

    bae_shifts = []
    share = share_repository.get_share_by_guest_id(db=db, guest_id=current_user.id)
    if share:
        bae_db_shifts = shift_repository.get_user_shifts_details(db=db, user_id=share.owner_id)
        for shift in bae_db_shifts:
            if str(shift.date.date()) == date_string:
                bae_shifts.append(shift)

    context = {
        "request": request,
        "date": {
            "date": date_string,
            "shifts": shifts,
            "day_number": int(date_segments[2]),
            "bae_shifts": bae_shifts,
            },
    }

    return templates.TemplateResponse(
        request=request,
        name="/webapp/home/calendar-card-simple.html",
        context=context,
    )