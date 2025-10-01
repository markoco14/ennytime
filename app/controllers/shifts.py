from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates
from app.handlers.shifts.delete_shift import handle_delete_shift
from app.handlers.shifts.get_shifts_new import handle_get_shifts_new
from app.handlers.shifts.get_shifts_page import handle_get_shifts_page
from app.handlers.shifts.get_shifts_setup import handle_get_shifts_setup
from app.handlers.shifts.post_shifts_new import handle_post_shifts_new
from app.models.db_shift_type import DbShiftType
from app.models.user_model import DBUser

router = APIRouter(prefix="/shifts")


def index(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    return handle_get_shifts_page(request, current_user, db)


def new(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    return handle_get_shifts_new(request, current_user, db)


def create(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    shift_name: Annotated[str, Form()],
    date_string: Annotated[str, Form()] = None,
    ):
    return handle_post_shifts_new(request, current_user, shift_name, date_string, db)

def edit(
    request: Request,
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    db: Annotated[Session, Depends(get_db)],
    shift_type_id: int
):
    if not current_user:
        response = "Uh Oh"

        return response
    
    db_shift = db.query(DbShiftType).filter(DbShiftType.id == shift_type_id).first()
    
    if not db_shift:
        return "No shift"

    response = templates.TemplateResponse(
        name="shifts/edit/index.html",
        context={
            "request": request,
            "shift_type": db_shift,
            "current_user": current_user
        }
    )

    if request.headers.get("hx-request"):
        response.headers["HX-Push-Url"] = f"shifts/{shift_type_id}/edit"

    return response

def update(
    request: Request,
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    db: Annotated[Session, Depends(get_db)],
    long_name: Annotated[str, Form(...)],
    short_name: Annotated[str, Form(...)],
    shift_type_id: int
):
    if not current_user:
        response = "Uh Oh"

        return response
        
    db_shift_type = db.query(DbShiftType).filter(DbShiftType.id == shift_type_id).first()

    db_shift_type.long_name = long_name
    db_shift_type.short_name = short_name

    db.commit()

    if request.headers.get("hx-request"):
        response = templates.TemplateResponse(
            name="shifts/edit/_form.html",
            context={
                "request": request,
                "shift_type": db_shift_type,
                "current_user": current_user
            }
        )

        return response
    
    response = templates.TemplateResponse(
        name="shifts/edit/index.html",
        context={
            "request": request,
            "shift_type": db_shift_type,
        }
    )
    
    return response


def delete(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    shift_type_id: int
):
    return handle_delete_shift(request, current_user, shift_type_id, db)


def setup(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    return handle_get_shifts_setup(request, current_user, db)