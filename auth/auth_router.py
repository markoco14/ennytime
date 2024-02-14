"""User authentication routes"""

from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from auth import auth_service
from core.database import get_db
from core.memory_db import SESSIONS, USERS
from schemas import CreateUserSession, Session, User, CreateUserHashed
from repositories import user_repository, session_repository

router = APIRouter()
templates = Jinja2Templates(directory="templates")


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
    
    # create new user with encrypted password
    new_user = CreateUserHashed(email=email, hashed_password=hashed_password)
    # add user to USERS
    app_user = user_repository.create_user(db=db, user=new_user)
    # USERS.update({email: new_user})

    # return response with session cookie and redirect to index
    session_cookie = auth_service.generate_session_token()
    new_session = CreateUserSession(
        session_id=session_cookie,
        user_id=app_user.id,
        expires_at=auth_service.generate_session_expiry()
    )
    # add session to SESSIONS 
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

    new_session = CreateUserSession(
        session_id=session_cookie,
        user_id=db_user.id,
        expires_at=auth_service.generate_session_expiry()
    )
    # add session to SESSIONS 
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