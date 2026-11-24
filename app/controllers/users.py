import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import requires_profile_owner, requires_user
from app.models.user import User
from app.viewmodels.pages import ProfilePage

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

    if not form_data.get("display_name") and not form_data.get("app_username") and not form_data.get("birthday"):
        return Response(status_code=200, headers={"hx-refresh": "true"})


    db_user = User.get(user_id=user_id)
    db_user.update(form_data=form_data)
    
    return Response(status_code=200, headers={"hx-refresh": "true"})

    
def unique(
    request: Request,
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

    if app_username == "":
        context = {
            "username": current_user.username if current_user.username else "",
            "current_user": current_user,
            "is_empty_username": True
        }

        return templates.TemplateResponse(
            request=request,
            name="profile/username-edit-errors.html",
            context=context
        )

    if app_username == current_user.username:
        return Response(status_code=200, headers={"hx-refresh": "true"})

    username_taken = User.username_exists(username=app_username)

    context = {
        "request": request,
        "current_user": current_user,
        "username": app_username,
        "is_username_taken": username_taken
    }

    return templates.TemplateResponse(
        request=request,
        name="profile/username-edit-errors.html",
        context=context
    )


def get_delete_form(request: Request, current_user=Depends(requires_user)):
    return templates.TemplateResponse(
        request=request,
        name="profile/delete/index.html",
        context={
            "current_user": current_user
        }

    )


async def confirm_delete(request: Request):
    form_data = await request.form()

    confirmation = form_data.get("confirmation", "")
    if not confirmation or confirmation != "Delete my account":
        return templates.TemplateResponse(
            request=request,
            name="profile/delete/submit-btn.html",
            context={
                "enabled": False
            }
        )
    
    return templates.TemplateResponse(
        request=request,
        name="profile/delete/submit-btn.html",
        context={
            "enabled": True
        }
    )


async def delete(request: Request, current_user=Depends(requires_user)):
    form_data = await request.form()
    
    confirmation = form_data.get("confirmation", "")
    if not confirmation or confirmation != "Delete my account":
        return templates.TemplateResponse(
            request=request,
            name="profile/delete/form-fields.html",
            context={
                "error_message": 'You need to copy "Delete my account" exactly'
            }
        )

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("DELETE FROM sessions WHERE user_id = :user_id;", {"user_id": current_user.id})
        conn.execute("DELETE FROM schedules WHERE user_id = :user_id;", {"user_id": current_user.id})
        conn.execute("DELETE FROM holiday_message WHERE sender_id = :user_id OR recipient_id = :user_id;", {"user_id": current_user.id})
        conn.execute("DELETE FROM user_signins WHERE user_id = :user_id;", {"user_id": current_user.id})
        conn.execute("DELETE FROM shifts WHERE user_id = :user_id;", {"user_id": current_user.id})
        conn.execute("DELETE FROM users WHERE id = :user_id;", {"user_id": current_user.id})
    
    response = Response(status_code=204, headers={"Hx-Redirect": "/account-deleted"})
    response.delete_cookie("session-id")
    return response


def deleted(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="profile/delete/deleted.html",
        context={}
    )