
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth import auth_service
from app.core.database import get_db

from app.repositories import shift_type_repository
from app import schemas

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.post("/register-shift-type", response_class=HTMLResponse)
def register_shift_type(
    request: Request,
    shift_type: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],):
    """Register shift type"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )
    # get the session data
    session_data: Session = auth_service.get_session_data(
        db=db,
        session_token=request.cookies.get("session-id")
        )
    # get the current user
    current_user: schemas.AppUser = auth_service.get_current_user(
        db=db,
        user_id=session_data.user_id
        )
    
    # get new shift type data ready
    new_shift_type = schemas.CreateShiftType(
        type=shift_type,
        user_id=current_user.id
    )

    # create new shift type or return an error
    try:
        shift_type_repository.create_shift_type(
            db=db,
            shift_type=new_shift_type
            )
    except IntegrityError:
        return templates.TemplateResponse(
            request=request,
            name="shifts/shift-list.html",
            context={"error": "Something went wrong."}
        )

    # get the new shift type list
    shift_types = shift_type_repository.list_user_shift_types(
        db=db,
        user_id=current_user.id
        )
    
    context={
        "request": request,
        "shift_types": shift_types,
          }

    return templates.TemplateResponse(
        request=request,
        name="shifts/shift-list.html", # change to list template
        context=context
    )

@router.delete("/delete-shift-type/{shift_type_id}", response_class=HTMLResponse | Response)
def delete_shift_type(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    shift_type_id: int
    ):
    """Delete shift type"""
    shift_type_repository.delete_shift_type_and_relations(
        db=db,
        shift_type_id=shift_type_id
        )
    return Response(status_code=200)