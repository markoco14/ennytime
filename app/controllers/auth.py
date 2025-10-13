"""User authentication routes"""

import datetime
import sqlite3
import time
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse

from app.auth import auth_service
from app.core.template_utils import templates
from app.dependencies import requires_guest, requires_user
from app.models.session import Session
from app.viewmodels.session import SessionCreate
from app.viewmodels.structs import UserLoginRow, UserRow

router = APIRouter()


def get_signup_page(
    request: Request,
    current_user=Depends(requires_guest)
):
    """Go to the sign up page"""
    current_time = datetime.datetime.now()
    selected_year = current_time.year
    selected_month = current_time.month

    if current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/calendar/{selected_year}/{selected_month}"})
        else:
            return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")

    response = templates.TemplateResponse(
        request=request,
        name="auth/signup.html"
    )

    return response


def get_signin_page(
    request: Request,
    current_user=Depends(requires_guest),
):
    """Go to the sign in page"""
    current_time = datetime.datetime.now()
    selected_year = current_time.year
    selected_month = current_time.month

    if current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/calendar/{selected_year}/{selected_month}"})
        else:
            return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")

    response = templates.TemplateResponse(
        request=request,
        name="auth/signin.html"
    )

    return response



def signup(
    request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    current_user=Depends(requires_guest),
    ):
    """Sign up a user"""
    # check if user exists
    current_time = datetime.datetime.now()
    selected_year = current_time.year
    selected_month = current_time.month

    if current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/calendar/{selected_year}/{selected_month}"})
        else:
            return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")
    
    # store username in email for readability
    email = username

    context = {
        "request": request,
        "previous_email": email,
        "previous_password": password
    }
    
    # check if email is valid
    if not auth_service.is_valid_email(email=email):
        context.update({"email_error": "Please enter a valid email."})
    
    # check if password is proper length
    if len(password) < 8: 
        context.update({"password_error": "Password must be at least 8 characters long."})

    # check if email already exists for this app
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT id, display_name, email, is_admin, birthday, username FROM users WHERE email = ?", (email, ))
        user_row = cursor.fetchone()

    if user_row:
        context.update({"form_error": "Invalid email or password"})

    if context.get("form_error") or context.get("email_error") or context.get("password_error"):
        response = templates.TemplateResponse(
            name="/auth/forms/sign-up-form.html",
            context=context)
        
        return response
    
    # Hash password
    hashed_password = auth_service.get_password_hash(password)
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, hashed_password) VALUES (?, ?);", (email, hashed_password))
        new_user_id = cursor.lastrowid

    token = str(uuid.uuid4())
    expires_at = int(time.time()) + 3600
    # use new_user_id from INSERT user
    session_create = SessionCreate(
        token=token,
        user_id=new_user_id,
        expires_at=expires_at
    )
    Session.create(data=session_create)
    
    response = Response(status_code=200)
    response.set_cookie(
        key="session-id",
        value=token,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    current_time = datetime.datetime.now()
    selected_year = current_time.year
    selected_month = current_time.month
    response.headers["HX-Redirect"] = f"/calendar/{selected_year}/{selected_month}"
    return response


def signin(
    request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    current_user=Depends(requires_guest),
    ):
    """Sign in a user"""
    current_time = datetime.datetime.now()
    selected_year = current_time.year
    selected_month = current_time.month

    if current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/calendar/{selected_year}/{selected_month}"})
        else:
            return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")

    # for readability
    email=username

    # context updated with errors later
    context = {
        "request": request,
        "previous_email": email,
        "previous_password": password
    }
    # check if email already exists for this app
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT id, display_name, email, is_admin, birthday, username, hashed_password FROM users WHERE email = ?", (email, ))
        user_row = cursor.fetchone()
        if user_row:
            current_user = UserLoginRow(*user_row)
        else:
            context.update({"form_error": "Invalid email or password"})

    
    # need to check if password is correct
    if current_user and not auth_service.verify_password(
        plain_password=password,
        hashed_password=current_user.hashed_password
    ):
        context.update({"form_error": "Invalid email or password"})

    # can also check if email is valid
    if not auth_service.is_valid_email(email=email):
        context.update({"email_error": "Please enter a valid email."})
    
    # check if password is proper length
    if len(password) < 8: 
        context.update({"password_error": "Password must be at least 8 characters long."})

    if context.get("form_error") or context.get("email_error") or context.get("password_error"):
        response = templates.TemplateResponse(
            name="/auth/forms/sign-in-form.html",
            context=context)
        
        return response

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("SELECT id, display_name, email, is_admin, birthday, username FROM users WHERE email = ?", (email, ))
        current_user = UserRow(*cursor.fetchone())

    token = str(uuid.uuid4())
    expires_at = int(time.time()) + 3600
    # use current_user because available
    session_create = SessionCreate(
        token=token,
        user_id=current_user.id,
        expires_at=expires_at
    )
    Session.create(data=session_create)

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_signins (user_id, status) VALUES (?, ?);", (current_user.id, "SUCCESS"))
    
    response = Response(status_code=200)
    response.set_cookie(
        key="session-id",
        value=token,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    current_time = datetime.datetime.now()
    selected_year = current_time.year
    selected_month = current_time.month
    response.headers["HX-Redirect"] = f"/calendar/{selected_year}/{selected_month}"
    return response


def signout(
        request: Request, 
        current_user=Depends(requires_user),
        ):
    """Sign out a user"""
    if not current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")
        
    session_id = request.cookies.get("session-id")

    db_session = Session.get_by_token(token=session_id)
    if not db_session:
        return RedirectResponse(status_code=303, url="/")
    
    db_session.delete()

    if request.headers.get("hx-request"):
        response = Response(status_code=200, headers={"hx-redirect": "/signin"})
    else:
        response = RedirectResponse(status_code=303, url="/signin")

    response.delete_cookie(key="session-id")
    return response