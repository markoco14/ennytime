
from typing import Annotated
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
from repositories import shift_repository

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/register-shift", response_class=HTMLResponse)
def schedule_shift(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
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
    
    session_data: Session = auth_service.get_session_data(db=db, session_token=request.cookies.get("session-id"))

    current_user: User = auth_service.get_current_user(db=db, user_id=session_data.user_id)
  
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
    

    db_shift = CreateShift(
        type_id=shift_type,
        user_id=current_user.id,
        date=datetime.datetime(int(date_segments[0]), int(date_segments[1]), int(date_segments[2]))
    )
    
    shift_repository.create_shift(db=db, shift=db_shift)

    context={"request": request}
    
    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context=context
    )