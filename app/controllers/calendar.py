"""
Calendar related routes
"""
from typing import Annotated, Optional
import datetime

from sqlalchemy.orm import Session
from fastapi import Depends, Request, Response

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates, block_templates
from app.handlers.calendar.get_calendar import get_calendar
from app.handlers.get_calendar_day_edit import handle_get_calendar_day_edit
from app.models.user_model import DBUser
from app.repositories import shift_repository
from app.repositories import shift_type_repository
from app.schemas import schemas
from app.dependencies import requires_user

def month(
    request: Request,
    month: int,
    year: int,
    day: Optional[int] = None,
    current_user=Depends(requires_user),
):  
    if not day:
        day = None

    return get_calendar(request=request, year=year, month=month, day=day, current_user=current_user)


def day(
    request: Request,
    month: int,
    year: int,
    day: int,
    current_user=Depends(requires_user),
):
    if not day:
        day = None

    return get_calendar(request=request, year=year, month=month, day=day, current_user=current_user)


def edit(
    request: Request,
    month: int,
    year: int,
    day: int,
    current_user=Depends(requires_user),
):
    if not day:
        day = None

    return get_calendar(request=request, year=year, month=month, day=day, current_user=current_user)


def get_calendar_day_edit(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    year: int,
    month: int,
    day: int
):
    return handle_get_calendar_day_edit(request=request, current_user=current_user, year=year, month=month, day=day, db=db)


def get_calendar_card_edit(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    date_string: str,
    shift_type_id: int,
):
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response
    # check if shift already exists
    # if exists delete, user will already have clicked a confirm on the frontend

    date_segments = date_string.split("-")
    db_shift = schemas.CreateShift(
        type_id=shift_type_id,
        user_id=current_user.id,
        date=datetime.datetime(int(date_segments[0]), int(
            date_segments[1]), int(date_segments[2]))
    )

    new_shift = shift_repository.create_shift(db=db, shift=db_shift)

    shift_type = shift_type_repository.get_user_shift_type(
        db=db, user_id=current_user.id, shift_type_id=shift_type_id)

    context = {
        "current_user": current_user,
        "request": request,
        "date_string": date_string,
        "shift_type": shift_type
    }

    return block_templates.TemplateResponse(
        name="/calendar/fragments/edit-view.html",
        context=context,
        block_name="shift_exists_button"
    )


async def delete_shift_for_date(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    date_string: str,
    shift_type_id: int,
):
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)

    # check if shift already exists
    # if exists delete, user will already have clicked a confirm on the frontend
    date_segments = date_string.split("-")
    date_object = datetime.datetime(
        int(date_segments[0]), int(date_segments[1]), int(date_segments[2]))

    existing_shift = shift_repository.get_user_shift(
        db=db, user_id=current_user.id, type_id=shift_type_id, date_object=date_object)

    if not existing_shift:
        return Response(status_code=404)

    shift_repository.delete_user_shift(db=db, shift_id=existing_shift.id)
    shift_type = shift_type_repository.get_user_shift_type(
        db=db, user_id=current_user.id, shift_type_id=shift_type_id)
    context = {
        "current_user": current_user,
        "request": request,
        "date_string": date_string,
        "shift_type": shift_type
    }

    return block_templates.TemplateResponse(
        name="/calendar/fragments/edit-view.html",
        context=context,
        block_name="no_shift_button"
    )
