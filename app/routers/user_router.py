
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth import auth_service
from app.core.database import get_db
from app.repositories import shift_repository, shift_type_repository
from app.repositories import user_repository, share_repository
from app.schemas import schemas
from app.services import calendar_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/profile", response_class=HTMLResponse | Response)
def get_profile_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)]
):
    """Profile page"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/signin.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: Session = auth_service.get_session_data(
        db=db,
        session_token=request.cookies.get("session-id")
    )

    try:
        current_user: schemas.User = auth_service.get_current_user(
            db=db,
            user_id=session_data.user_id
        )
    except AttributeError:
        # TODO: figure out how to specify because may be other errors
        # although this response may just be fine
        # AttributeError: 'NoneType' object has no attribute 'user_id'
        response = templates.TemplateResponse(
            request=request,
            name="website/signin.html",
            headers={"HX-Redirect": "/signin"},
        )
        response.delete_cookie("session-id")
        return response

    shift_types = shift_type_repository.list_user_shift_types(
        db=db,
        user_id=current_user.id)

    shifts = shift_repository.get_user_shifts(db=db, user_id=current_user.id)
    for shift in shifts:
        shift.type = shift_type_repository.get_user_shift_type(
            db=db,
            user_id=current_user.id,
            shift_type_id=shift.type_id
        )
        shift.date = f"{calendar_service.MONTHS[shift.date.month - 1]}  {calendar_service.get_current_day(shift.date.day)}, {shift.date.year}"

    share_headings = ["Name", "Actions"]
    shift_headings = ["Type", "Date", "Actions"]
    
    if current_user.display_name is not None:
        display_name = current_user.display_name.split(" ")[0]
    else:
        display_name = "NewUser00001"

    user_page_data = {
        "display_name": display_name,
        "is_admin": current_user.is_admin
    }

    context = {
        "user_data": user_page_data,
        "request": request,
        "shift_types": shift_types,
        "user": current_user,
        "shifts": shifts,
        "share_headings": share_headings,
        "shift_headings": shift_headings,
    }

    # TODO: refactor this to use a service
    # don't send the whole user db model to the front end
    # hashed passwords are there
    share_owner = share_repository.get_share_by_owner_id(
        db=db, user_id=current_user.id)

    if not share_owner:
        return templates.TemplateResponse(
            request=request,
            name="webapp/profile/profile-page.html",
            context=context
        )

    share_user = user_repository.get_user_by_id(
        db=db, user_id=share_owner.guest_id)
    context.update({"share": share_owner, "share_user": share_user})
    return templates.TemplateResponse(
        request=request,
        name="webapp/profile/profile-page.html",
        context=context
    )


@router.get("/contact/{user_id}", response_class=HTMLResponse | Response)
def get_display_name_widget(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: Session = auth_service.get_session_data(
        db=db,
        session_token=request.cookies.get("session-id")
    )

    current_user: schemas.User = auth_service.get_current_user(
        db=db,
        user_id=session_data.user_id
    )

    if current_user.id != user_id:
        return Response(status_code=403)

    context = {
        "request": request,
        "user": current_user,
    }
    return templates.TemplateResponse(
        request=request,
        name="webapp/profile/display-name.html",
        context=context
    )


def update_entity(original_entity, update_data: dict[str, any]):
    """
    General function for updating an entity with the values available in input dictionary
    """
    for key, value in update_data.items():
        setattr(original_entity, key, value)

    return original_entity


@router.put("/contact/{user_id}", response_class=HTMLResponse | Response)
def update_user_contact(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    display_name: Annotated[str, Form()] = None,
):
    """ update user attribute"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: Session = auth_service.get_session_data(
        db=db,
        session_token=request.cookies.get("session-id")
    )

    current_user: schemas.User = auth_service.get_current_user(
        db=db,
        user_id=session_data.user_id
    )

    if current_user.id != user_id:
        return Response(status_code=403)

    update_data = {}
    if display_name is not None:
        update_data.update({"display_name": display_name})

    updated_user = update_entity(
        original_entity=current_user,
        update_data=update_data
    )

    try:
        user_repository.patch_user(
            db=db,
            updated_user=updated_user)
    except IntegrityError:
        context = {
            "request": request,
            "user": current_user,
        }

        return templates.TemplateResponse(
            request=request,
            name="webapp/profile/display-name.html",
            context=context
        )

    context = {
        "request": request,
        "user": updated_user,
    }

    return templates.TemplateResponse(
        request=request,
        name="webapp/profile/display-name.html",
        context=context
    )


@router.get("/contact/{user_id}/edit", response_class=HTMLResponse | Response)
def get_edit_display_name_widget(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Edit contact page"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: Session = auth_service.get_session_data(
        db=db,
        session_token=request.cookies.get("session-id")
    )

    current_user: schemas.User = auth_service.get_current_user(
        db=db,
        user_id=session_data.user_id
    )

    if current_user.id != user_id:
        return Response(status_code=403)

    context = {
        "request": request,
        "user": current_user,
    }

    return templates.TemplateResponse(
        request=request,
        name="webapp/profile/display-name-edit.html",
        context=context
    )
