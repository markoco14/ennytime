"""
Calendar related routes
"""
import logging
import time
from typing import Annotated, Optional
from pprint import pprint
import datetime

from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates, block_templates
from app.handlers.get_calendar import handle_get_calendar
from app.handlers.get_calendar_card_detail import handle_get_calendar_card_detail
from app.handlers.get_calendar_card_simple import handle_get_calendar_card_simple
from app.handlers.get_calendar_day import handle_get_calendar_day
from app.handlers.get_calendar_day_edit import handle_get_calendar_day_edit
from app.models.user_model import DBUser
from app.repositories import share_repository, shift_repository
from app.repositories import shift_type_repository
from app.schemas import schemas
from app.services import calendar_service

def month(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    month: Optional[int] = None,
    year: Optional[int] = None,
):
    return handle_get_calendar(request=request, current_user=current_user, month=month, year=year, db=db)


def day(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    year: int,
    month: int,
    day: int
):
    return handle_get_calendar_day(request=request, current_user=current_user, year=year, month=month, day=day, db=db)