
from typing import Annotated
import datetime
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth import auth_service
from app.core.database import get_db
from app.models.user_model import DBUser
from app.schemas import schemas
from app.repositories import shift_repository, shift_type_repository, share_repository, user_repository
from app.services import calendar_service, chat_service

router = APIRouter(prefix="/shifts")
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")

# Custom filter to check if a shift type is in user shifts


def is_user_shift(shift_type_id, shifts):
    return any(shift['type_id'] == shift_type_id for shift in shifts)


# Add the custom filter to Jinja2 environment
templates.env.filters['is_user_shift'] = is_user_shift
block_templates.env.filters['is_user_shift'] = is_user_shift

@router.get("/")
def get_shifts_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response
    
    shift_types = shift_type_repository.list_user_shift_types(
        db=db, user_id=current_user.id)
    if not shift_types:
        response = RedirectResponse(status_code=303, url="/shifts/setup") 
        return response
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "message_count": message_count,
        "shift_types": shift_types
    }
    
    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="/shifts/fragments/shift-type-list.html",
            context=context
        )

        return response


    response = templates.TemplateResponse(
        name="/shifts/index.html",
        context=context
    )

    return response


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
    
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "message_count": message_count,
    }

    response = templates.TemplateResponse(
        name="/shifts/pages/setup.html",
        context=context
    )

    return response

@router.get("/new")
def get_shift_manager_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response
    
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "message_count": message_count
    }

    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="shifts/shift-type-form.html",
            context=context
        )
        return response

    response = templates.TemplateResponse(
        name="shifts/pages/new.html",
        context=context
    )
    return response

@router.post("/new")
def store_shift_type(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    shift_name: Annotated[str, Form()],
    ):
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response
    
    long_name_split = shift_name.split(" ")
    short_name = ""
    for part in long_name_split:
        short_name += part[0].upper()

    # get new shift type data ready
    new_shift_type = schemas.CreateShiftType(
        long_name=shift_name,
        short_name=short_name,
        user_id=current_user.id
    )

    # create new shift type or return an error
    shift_type_repository.create_shift_type(
        db=db,
        shift_type=new_shift_type
    )
    
    # TODO: change this to return single shift type and animate it into the list
    # get the new shift type list
    shift_types = shift_type_repository.list_user_shift_types(
        db=db,
        user_id=current_user.id
    )

    context = {
        "request": request,
        "shift_types": shift_types,
    }
    # TODO: change to /shifts when route up and running
    response = Response(status_code=303)
    response.headers["HX-Redirect"] = "/shifts"

    return response

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
