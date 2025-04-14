from typing import Annotated
import re

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import Response, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
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
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response
    
    shift_types = shift_type_repository.list_user_shift_types(
        db=db, user_id=current_user.id)
    if not shift_types:
        response = RedirectResponse(status_code=303, url="/shifts/setup") 
        return response
    
    # get chatroom id to link directly from the chat icon
    # get unread message count so chat icon can display the count on page load
    user_chat_data = chat_service.get_user_chat_data(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "chat_data": user_chat_data,
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
    
    user_chat_data = chat_service.get_user_chat_data(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "chat_data": user_chat_data
    }

    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="shifts/new/partials/form.html",
            context=context
        )
        return response

    response = templates.TemplateResponse(
        name="shifts/new/index.html",
        context=context
    )
    return response

@router.post("/new")
def store_shift_type(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)],
    shift_name: Annotated[str, Form()],
    date_string: Annotated[str, Form()] = None,
    ):
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response
    
    # clean up shift name
    cleaned_shift_name = shift_name.strip()
    space_finder_regex = re.compile(r"\s+")
    cleaned_shift_name = re.sub(space_finder_regex, ' ', cleaned_shift_name)
   
    # create short name
    long_name_split = cleaned_shift_name.split(" ")
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

    hx_current_url = request.headers.get("hx-current-url") or None
    from_setup_page = "/shifts/setup" in hx_current_url
    from_new_page = "/shifts/new" in hx_current_url
    if from_new_page or from_setup_page:
        response = Response(status_code=303)
        response.headers["HX-Redirect"] = "/shifts"

        return response
    
    context.update({"date_string": date_string})
    response = templates.TemplateResponse(
        name="/calendar/fragments/edit-view.html",
        context=context
        )
    
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
