"""
Calendar related routes
"""
from typing import Optional

from fastapi import Depends, Request

from app.handlers.calendar.get_calendar import get_calendar
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
