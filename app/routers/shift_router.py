from typing import Annotated
import re

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.handlers.shifts.get_shifts_new import handle_get_shifts_new
from app.handlers.shifts.get_shifts_page import handle_get_shifts_page
from app.handlers.shifts.post_shifts_new import handle_post_shifts_new
from app.models.user_model import DBUser
from app.schemas import schemas
from app.repositories import shift_type_repository
from app.services import chat_service

router = APIRouter(prefix="/shifts")
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")

# Custom filter to check if a shift type is in user shifts


def is_user_shift(shift_type_id, shifts):
    return any(shift['type_id'] == shift_type_id for shift in shifts)


# Add the custom filter to Jinja2 environment
templates.env.filters['is_user_shift'] = is_user_shift
block_templates.env.filters['is_user_shift'] = is_user_shift

@router.get("")
def get_shifts_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    return handle_get_shifts_page(request, current_user, db)


@router.get("/setup")
def get_shifts_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response

    user_chat_data = chat_service.get_user_chat_data(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "chat_data": user_chat_data,
    }

    response = templates.TemplateResponse(
        name="/shifts/setup/index.html",
        context=context
    )

    return response


@router.get("/new")
def get_shift_manager_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    return handle_get_shifts_new(request, current_user, db)


@router.post("/new")
def store_shift_type(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    shift_name: Annotated[str, Form()],
    date_string: Annotated[str, Form()] = None,
    ):
    return handle_post_shifts_new(request, current_user, shift_name, date_string, db)


@router.delete("/{shift_type_id}")
def delete_shift_type(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    shift_type_id: int
):
    """Delete shift type"""
    response = Response(
        status_code=200,
    )
    shift_type_repository.delete_shift_type_and_relations(
        db=db,
        shift_type_id=shift_type_id
    )
    
    shift_types = shift_type_repository.list_user_shift_types(db=db, user_id=current_user.id)

    if not shift_types:
        response.headers["HX-Redirect"] = "/shifts/setup/"
        
    return response
