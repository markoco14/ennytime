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
    
    if form_data.get("birthday"):
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET birthday = ? WHERE id = ?;", (form_data.get("birthday"), user_id, ))
        return Response(status_code=200, headers={"hx-refresh": "true"})
    

    return "ok"


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
