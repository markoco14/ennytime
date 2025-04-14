from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.handlers.shifts.delete_shift import handle_delete_shift
from app.handlers.shifts.get_shifts_new import handle_get_shifts_new
from app.handlers.shifts.get_shifts_page import handle_get_shifts_page
from app.handlers.shifts.get_shifts_setup import handle_get_shifts_setup
from app.handlers.shifts.post_shifts_new import handle_post_shifts_new
from app.models.user_model import DBUser

router = APIRouter(prefix="/shifts")


@router.get("")
def get_shifts_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    return handle_get_shifts_page(request, current_user, db)


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
    return handle_delete_shift(request, current_user, shift_type_id, db)


@router.get("/setup")
def get_shifts_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    return handle_get_shifts_setup(request, current_user, db)