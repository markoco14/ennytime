
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from jinja2_fragments.fastapi import Jinja2Blocks

from app.auth import auth_service
from app.core.database import get_db

from app.repositories import shift_type_repository
from app.schemas import schemas

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/shift-types", response_class=HTMLResponse)
def get_shift_type_list(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies
    )
    if not current_user:
        return Response(status_code=401)
    
    db_shift_types = shift_type_repository.list_user_shift_types(
        db=db,
        user_id=current_user.id
    )

    context = {
        "request": request,
        "shift_types": db_shift_types,
        "current_user": current_user
    }

    return block_templates.TemplateResponse(
        name="profile/sections/shift-type-section.html",
        context=context,
        block_name="shift_type_list"
    )
    
@router.get("/shift-types/new", response_class=HTMLResponse)
def get_new_shift_type_form(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies
    )
    if not current_user:
        return Response(status_code=401)

    context = {
        "request": request,
        "current_user": current_user
    }

    return templates.TemplateResponse(
        "profile/shift-type-form.html",
        context=context
    )
    


@router.post("/shift-types/new", response_class=HTMLResponse)
def register_shift_type(
        request: Request,
        long_name: Annotated[str, Form()],
        short_name: Annotated[str, Form()],
        db: Annotated[Session, Depends(get_db)],):
    """Register shift type"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
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
        long_name=long_name,
        short_name=short_name,
        user_id=current_user.id
    )

    # create new shift type or return an error
    try:
        shift_type_repository.create_shift_type(
            db=db,
            shift_type=new_shift_type
        )
    except IntegrityError:

        return block_templates.TemplateResponse(
            name="profile/sections/shift-type-section.html",
            context={"request": request, "error": "Something went wrong."},
            block_name="shift_type_list"
        )

    # get the new shift type list
    shift_types = shift_type_repository.list_user_shift_types(
        db=db,
        user_id=current_user.id
    )

    context = {
        "request": request,
        "shift_types": shift_types,
    }

    return block_templates.TemplateResponse(
        name="profile/sections/shift-type-section.html",
        context=context,
        block_name="shift_type_list"
    )


@router.delete("/delete-shift-type/{shift_type_id}", response_class=HTMLResponse | Response)
def delete_shift_type(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    shift_type_id: int
):
    """Delete shift type"""
    response = Response(
        status_code=200,
        headers={"HX-Trigger": "getShiftTable"}
    )
    shift_type_repository.delete_shift_type_and_relations(
        db=db,
        shift_type_id=shift_type_id
    )
    return response
