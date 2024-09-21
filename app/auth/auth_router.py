"""User authentication routes"""

import random
from typing import Annotated


from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db

from app.schemas import schemas
from app.repositories import session_repository

from app.repositories import user_repository

router = APIRouter()
templates = Jinja2Templates(directory="templates")



@router.post("/user/email", response_class=HTMLResponse)
def validate_email(
    request: Request,
    username: Annotated[str, Form(...)] = ''
):
    email = username
    context = {
        "request": request,
        "email_error": "",
        "previous_email": email
    }
    
    if email == '':
        response = templates.TemplateResponse(
            name="/auth/forms/email-input.html",
            context=context
            )
        return response
        
    if not auth_service.is_valid_email(email=email):
        context.update({"email_error": "Please enter a valid email."})
        response = templates.TemplateResponse(
            name="/auth/forms/email-input.html",
            context=context
            )
        return response
    
    response = templates.TemplateResponse(
        name="/auth/forms/email-input.html",
        context=context
        )
    return response


@router.post("/user/password", response_class=HTMLResponse)
def validate_password(
    request: Request,
    password: Annotated[str, Form(...)] = ''
):
    context = {
        "request": request,
        "password_error": "",
        "previous_password": password
    }

    if password == '':
        response = templates.TemplateResponse(
            name="/auth/forms/password-input.html",
            context=context
            )
        return response
    
    if len(password) < 8:
        context.update({"password_error": "Password must be at least 8 characters long"})
        response = templates.TemplateResponse(
            name="/auth/forms/password-input.html",
            context=context
            )
        return response
    
    response = templates.TemplateResponse(
            name="/auth/forms/password-input.html",
            context=context
            )
    return response    

@router.post("/signup", response_class=Response)
def signup(
    request: Request,
    response: Response,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    ):
    """Sign up a user"""
    # check if user exists
    # db_user: User = USERS.get(email)
    db_user = user_repository.get_user_by_email(db=db, email=email)
    # return db_user
    if db_user:
        return templates.TemplateResponse(
            request=request,
            name="/auth/form-error.html",
            context={"request": request, "error": "Invalid email or password."}
        )
    # Hash password
    hashed_password = auth_service.get_password_hash(password)
    
    # give the user a display name
    display_name = f"NewUser{random.randint(1, 10000)}"
    
    # create new user with encrypted password
    new_user = schemas.CreateUserHashed(email=email, hashed_password=hashed_password, display_name=display_name)

    # add user to USERS
    app_user = user_repository.create_user(db=db, user=new_user)
    # USERS.update({email: new_user})

    # return response with session cookie and redirect to index
    session_cookie = auth_service.generate_session_token()
    new_session = schemas.CreateUserSession(
        session_id=session_cookie,
        user_id=app_user.id,
        expires_at=auth_service.generate_session_expiry()
    )
    # store user session
    session_repository.create_session(db=db, session=new_session)
    
    response = Response(status_code=200)
    response.set_cookie(
        key="session-id",
        value=session_cookie,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    response.headers["HX-Redirect"] = "/"

    return response


@router.post("/signin", response_class=Response)
def signin(
    request: Request,
    response: Response,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    ):
    """Sign in a user"""
    # check if user exists
    db_user = user_repository.get_user_by_email(db=db, email=email)
    if not db_user:
        return templates.TemplateResponse(
            request=request,
            name="/auth/form-error.html",
            context={"request": request, "error": "Invalid email or password."}
            
        )
    # verify the password
    if not auth_service.verify_password(
        plain_password=password,
        hashed_password=db_user.hashed_password
        ):
        return templates.TemplateResponse(
            request=request,
            name="/auth/form-error.html",
            context={"request": request, "error": "Invalid email or password"}
            
        )

    # return response with session cookie and redirect to index
    session_cookie = auth_service.generate_session_token()

    new_session = schemas.CreateUserSession(
        session_id=session_cookie,
        user_id=db_user.id,
        expires_at=auth_service.generate_session_expiry()
    )
    # store user session
    session_repository.create_session(db=db, session=new_session)
    
    response = Response(status_code=200)
    response.set_cookie(
        key="session-id",
        value=session_cookie,
        httponly=True,
        secure=True,
        samesite="Lax"
    )
    response.headers["HX-Redirect"] = "/"
    return response


@router.get("/signout", response_class=HTMLResponse)
def signout(request: Request, response: Response, db: Annotated[Session, Depends(get_db)],):
    """Sign out a user"""
    session_id = request.cookies.get("session-id")
    if session_id:
        session_repository.destroy_session(db=db, session_id=session_id)

    response = Response(status_code=200)
    response.delete_cookie(key="session-id")
    response.headers["HX-Redirect"] = "/signin"
    return response