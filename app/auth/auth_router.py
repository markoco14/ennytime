"""User authentication routes"""

import random
from typing import Annotated


from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.models.user_signin_model import DBUserSignin, SigninStatus
from app.schemas import schemas
from app.repositories import session_repository

from app.repositories import user_repository

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/signup", response_class=HTMLResponse)
def get_signup_page(
    request: Request,
    current_user=Depends(auth_service.user_dependency)
):
    """Go to the sign up page"""
    if current_user:
        return RedirectResponse(url="/")

    response = templates.TemplateResponse(
        request=request,
        name="auth/signup.html"
    )
    if request.cookies.get("session-id"):
        response.delete_cookie("session-id")

    return response

@router.get("/signin", response_class=HTMLResponse)
def get_signin_page(
    request: Request,
    current_user=Depends(auth_service.user_dependency)
):
    """Go to the sign in page"""
    if current_user:
        return RedirectResponse(url="/")

    response = templates.TemplateResponse(
        request=request,
        name="auth/signin.html"
    )
    if request.cookies.get("session-id"):
        response.delete_cookie("session-id")
    return response

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
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency),
    ):
    """Sign up a user"""
    # check if user exists
    if current_user:
        response = Response(status_code=303, content="Redirecting...")
        response.headers["HX-Redirect"] = "/"
        return response
    
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
    if user_repository.get_user_by_email(db=db, email=email):
        context.update({"form_error": "Invalid email or password"})

    if context.get("form_error") or context.get("email_error") or context.get("password_error"):
        response = templates.TemplateResponse(
            name="/auth/forms/sign-up-form.html",
            context=context)
        
        return response
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
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency),
    ):
    """Sign in a user"""
    # check if user exists
    if current_user:
        response = Response(status_code=303, content="Redirecting...")
        response.headers["HX-Redirect"] = "/"
        return response
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

    # return response with session cookie and redirect to index
    session_cookie = auth_service.generate_session_token()

    new_session = schemas.CreateUserSession(
        session_id=session_cookie,
        user_id=db_user.id,
        expires_at=auth_service.generate_session_expiry()
    )
    # store user session
    session_repository.create_session(db=db, session=new_session)
    
    ip_address = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    user_agent = request.headers.get("User-Agent")

    user_signin = DBUserSignin(
        user_id=db_user.id,  # Assuming you have the current user info
        ip_address=ip_address,
        user_agent=user_agent,
        status = SigninStatus.SUCCESS
    )

    db.add(user_signin)
    db.commit()
    db.refresh(user_signin)

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