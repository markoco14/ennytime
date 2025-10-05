from collections import namedtuple
import sqlite3
from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth import auth_service
from app.core.database import get_db

from app.dependencies import requires_profile_owner, requires_user
from app.repositories import user_repository
from app.schemas import schemas
from app.services import chat_service
from app.models.user_model import DBUser
from app.models.share_model import DbShare
from app.structs.pages import ProfilePage
from app.structs.structs import UserRow

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def profile(
    request: Request,
    current_user=Depends(requires_user),
):
    """Profile page"""
    if not current_user:
        if request.headers.get("hx-request"):
            response = Response(status_code=200, headers={"hx-redirect": f"/signin"})
        else:
            response = RedirectResponse(status_code=303, url=f"/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    context = ProfilePage(
        current_user=current_user,
    )
    

    return templates.TemplateResponse(
        request=request,
        name="profile/profile-page.html",
        context=context
    )


async def update(
    request: Request,
    user_id: int,
    current_user=Depends(requires_profile_owner),
):  
    """Updates a user resource"""
    if not current_user:
        if request.headers.get("hx-request"):
            response = Response(status_code=200, headers={"hx-redirect": f"/signin"})
        else:
            response = RedirectResponse(status_code=303, url=f"/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    form_data = await request.form()
    
    if form_data.get("display_name"):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET display_name = ? WHERE id = ?;", (form_data.get("display_name"), user_id, ))
        return Response(status_code=200, headers={"hx-refresh": "true"})
    
    if form_data.get("app_username"):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET username = ? WHERE id = ?;", (form_data.get("app_username"), user_id, ))
        return Response(status_code=200, headers={"hx-refresh": "true"})
    

    return "ok"

def display_name(
    request: Request,
    user_id: int,
    current_user=Depends(auth_service.user_dependency)
):
    if not current_user:
        response = JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
            headers={"HX-Trigger": 'unauthorizedRedirect'}
        )
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if current_user.id != user_id:
        return Response(status_code=403)

    context = {
        "current_user": current_user,
        "request": request,
        "user": current_user,
    }
    return templates.TemplateResponse(
        request=request,
        name="profile/display-name.html",
        context=context
    )


def update_entity(original_entity, update_data: dict[str, any]):
    """
    General function for updating an entity with the values available in input dictionary
    """
    for key, value in update_data.items():
        setattr(original_entity, key, value)

    return original_entity


def update_display_name(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    display_name: Annotated[str, Form()] = None,
    current_user=Depends(auth_service.user_dependency)
):
    """ update user attribute"""
    if not current_user:
        response = JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
            headers={"HX-Trigger": 'unauthorizedRedirect'}
        )
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if current_user.id != user_id:
        response = JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
            headers={"HX-Trigger": 'unauthorizedRedirect'}
        )
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    # if display name is empty
    # don't update
    # send back with last stored display name
    db_user = user_repository.get_user_by_id(db=db, user_id=current_user.id)
    context={"request": request, "user": db_user}

    if display_name == "":
        response = templates.TemplateResponse(
            name="profile/display-name-input.html",
            context=context
        )
        return response

    # display name not empty
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
            "user": db_user,
        }

        return templates.TemplateResponse(
            request=request,
            name="profile/display-name-input.html",
            context=context
        )
    


    context = {
        "request": request,
        "user": updated_user,
    }

    if current_user.display_name is None:
        context.update({"display_name": ""})
    else:
        context.update({"display_name": current_user.display_name})

    return templates.TemplateResponse(
        request=request,
        name="profile/display-name-input.html",
        context=context
    )


def edit(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency)
):
    """Edit contact page"""
    if not current_user:
        response = JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
            headers={"HX-Trigger": 'unauthorizedRedirect'}
        )
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if current_user.id != user_id:
        return Response(status_code=403)

    context = {
        "current_user": current_user,
        "request": request,
        "user": current_user,
    }

    return templates.TemplateResponse(
        request=request,
        name="profile/display-name-edit.html",
        context=context
    )


def birthday(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Edit birthday page"""
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
        "current_user": current_user,
        "request": request,
        "user": current_user,
    }
    if current_user.birthday is None:
        context.update({"birthday": "yyyy-MM-dd"})
    else:
        context.update({"birthday": current_user.birthday})

    return templates.TemplateResponse(
        request=request,
        name="profile/birthday.html",
        context=context
    )


def update_birthday(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    birthday: Annotated[str, Form()] = None,
):
    """Updates the user's birthday and returns success to front end"""
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

    if not birthday:
        return Response(status_code=200)

    current_user.birthday = birthday
    user_repository.patch_user(
        db=db,
        updated_user=current_user
    )
    context = {
        "current_user": current_user,
        "request": request,
        "user": current_user,
        "birthday": current_user.birthday
    }

    return templates.TemplateResponse(
        request=request,
        name="profile/birthday-input.html",
        context=context
    )


def birthday_edit(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    """Edit birthday widget"""
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
        "current_user": current_user,
        "request": request,
        "user": current_user,
    }

    return templates.TemplateResponse(
        request=request,
        name="profile/birthday-edit.html",
        context=context
    )


def username(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency)
):
    """Returns HTML to let the user edit their username"""
    if not current_user:
        response = RedirectResponse(url="/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if current_user.id != user_id:
        return Response(status_code=403)
    
    context = {
        "request": request,
        "user": current_user,
    }
    if current_user.username == None:
        context.update({"username": ""})
    else:
        context.update({"username": current_user.username})

    return templates.TemplateResponse(
        request=request,
        name="profile/username.html",
        context=context
    )


def update_username(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    app_username: Annotated[str, Form()] = None,
    current_user=Depends(auth_service.user_dependency)
):
    """Returns HTML to let the user edit their username"""
    if not current_user:
        response = RedirectResponse(url="/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if current_user.id != user_id:
        return Response(status_code=403)

    current_user.username = app_username
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    context = {
        "request": request,
        "user": current_user,
        "username": current_user.username
    }

    return templates.TemplateResponse(
        request=request,
        name="profile/username.html",
        context=context
    )

def unique(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    app_username: Annotated[str, Form()] = "",
    current_user=Depends(requires_user),  
):
    if not current_user:
        if request.headers.get("hx-request"):
            response = Response(status_code=200, headers={"hx-redirect": f"/signin"})
        else:
            response = RedirectResponse(status_code=303, url=f"/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    context = {
        "request": request,
        "current_user": current_user,
    }

    if app_username == "":
        context.update({"is_empty_username": True})
        if current_user.username:
            context.update({
                "username": current_user.username
            })
        else:
            context.update({
                "username": ""
            })


        return templates.TemplateResponse(
            request=request,
            name="profile/username-edit-errors.html",
            context=context
        )

    if app_username == current_user.username:
        context.update({
            "username": app_username,
            "is_users_username": True
        })

        return templates.TemplateResponse(
            request=request,
            name="profile/username-edit-errors.html",
            context=context
        )

    db_username = db.query(DBUser).filter(
        DBUser.username == app_username).first()

    if not db_username:
        username_taken = False
    else:
        username_taken = True

    context.update({          
        "username": app_username,
        "is_username_taken": username_taken
    })

    return templates.TemplateResponse(
        request=request,
        name="profile/username-edit-errors.html",
        context=context
    )
