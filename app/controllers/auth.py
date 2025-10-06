"""User authentication routes"""

import datetime
import sqlite3
import time
from typing import Annotated
import uuid


from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates

from app.repositories import user_repository
from app.dependencies import requires_guest, requires_user
from app.structs.structs import UserRow

router = APIRouter()


def get_signup_page(
    request: Request,
    lite_user=Depends(requires_guest)
):
    """Go to the sign up page"""
    current_time = datetime.datetime.now()
    selected_year = current_time.year
    selected_month = current_time.month

    if lite_user:
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
    lite_user=Depends(requires_guest),
):
    """Go to the sign in page"""
    current_time = datetime.datetime.now()
    selected_year = current_time.year
    selected_month = current_time.month

    if lite_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/calendar/{selected_year}/{selected_month}"})
        else:
            return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")

    response = templates.TemplateResponse(
        request=request,
        name="auth/signin.html"
    )

    return response


# def validate_email(
#     request: Request,
#     username: Annotated[str, Form(...)] = ''
# ):
#     email = username
#     context = {
#         "request": request,
#         "email_error": "",
#         "previous_email": email
#     }
    
#     if email == '':
#         response = templates.TemplateResponse(
#             name="/auth/forms/email-input.html",
#             context=context
#             )
#         return response
        
#     if not auth_service.is_valid_email(email=email):
#         context.update({"email_error": "Please enter a valid email."})
#         response = templates.TemplateResponse(
#             name="/auth/forms/email-input.html",
#             context=context
#             )
#         return response
    
#     response = templates.TemplateResponse(
#         name="/auth/forms/email-input.html",
#         context=context
#         )
#     return response


# def validate_password(
#     request: Request,
#     password: Annotated[str, Form(...)] = ''
# ):
#     context = {
#         "request": request,
#         "password_error": "",
#         "previous_password": password
#     }

#     if password == '':
#         response = templates.TemplateResponse(
#             name="/auth/forms/password-input.html",
#             context=context
#             )
#         return response
    
#     if len(password) < 8:
#         context.update({"password_error": "Password must be at least 8 characters long"})
#         response = templates.TemplateResponse(
#             name="/auth/forms/password-input.html",
#             context=context
#             )
#         return response
    
#     response = templates.TemplateResponse(
#             name="/auth/forms/password-input.html",
#             context=context
#             )
#     return response    


def signup(
    request: Request,
    response: Response,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    lite_user=Depends(requires_guest),
    ):
    """Sign up a user"""
    # check if user exists
    current_time = datetime.datetime.now()
    selected_year = current_time.year
    selected_month = current_time.month

    if lite_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/calendar/{selected_year}/{selected_month}"})
        else:
            return RedirectResponse(status_code=303, url=f"/calendar/{selected_year}/{selected_month}")
        
    # if current_user:
    #     response = Response(status_code=303, content="Redirecting...")
    #     response.headers["HX-Redirect"] = "/"
    #     return response
    
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
    new_session = (token, new_user_id, expires_at)
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", new_session)
    
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
    db: Annotated[Session, Depends(get_db)],
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

    # get user to check password against hashed password
    db_user = user_repository.get_user_by_email(db=db, email=email)
    if not db_user:
        context.update({"form_error": "Invalid email or password"})
    
    # need to check if password is correct
    if db_user and not auth_service.verify_password(
        plain_password=password,
        hashed_password=db_user.hashed_password
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
    new_session = (token, current_user.id, expires_at)
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", new_session)
    
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
    if session_id:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.execute("PRAGMA foreign_key=ON;")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE token = ?", (session_id, ))

    if request.headers.get("hx-request"):
        response = Response(status_code=200, headers={"hx-redirect": "/signin"})
    else:
        response = RedirectResponse(status_code=303, url="/signin")

    response.delete_cookie(key="session-id")
    return response