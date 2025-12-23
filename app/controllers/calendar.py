"""
Calendar related routes
"""
from typing import Annotated, Optional

from fastapi import Depends, Request, Response

from app.core.template_utils import templates
from app.core.config import get_settings
from app.handlers.calendar.get_calendar import get_calendar
from app.dependencies import requires_user
from app.viewmodels.user import CurrentUser

settings = get_settings()

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

def birthday_greeting(
        request: Request,
        current_user: Annotated[CurrentUser, Depends(requires_user)]
        ):
    if not current_user:
        return Response(status_code=401, content="No user")
    
    return templates.TemplateResponse(
        request=request,
        name="calendar/birthday-modal.html",
        context={"birthday_message": settings.BIRTHDAY_LINES},
    )

def close_greeting(request: Request, current_user: Annotated[CurrentUser, Depends(requires_user)]):
    return Response(status_code=200)

def close_holiday_modal(request: Request, current_user: Annotated[CurrentUser, Depends(requires_user)]):
    return Response(status_code=200)