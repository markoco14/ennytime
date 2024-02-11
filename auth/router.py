from typing import Annotated
from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from auth import auth_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")

class User(BaseModel):
    """User"""
    email: str
    password: str

USERS: dict[User] = {
    "johndoe@example.com": User(
        email="johndoe@example.com",
        password="fakehashedsecret"
        ),
    "alice@example.com": User(
        email="alice@example.com",
        password="fakehashedsecret"
        ),
    "mark.oconnor14@gmail.com": User(
        email="mark.oconnor14@gmail.com",
        password="$2b$12$.hJ1LOqpdFZldlwiSnDUUeorgtwjIB68u0tTZwD2kjPNjRIP0.tPK"
        ),
}

@router.post("/signup", response_class=Response)
def signup(
    request: Request,
    response: Response,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()]
    ):
    """Sign up a user"""
    # check if user exists
    db_user: User = USERS.get(email)
    if db_user:
        return templates.TemplateResponse(
            request=request,
            name="/auth/form-error.html",
            context={"request": request, "error": "Invalid email or password."}
        )
    # Hash password
    hashed_password = auth_service.get_password_hash(password)
    
    # create new user with encrypted password
    new_user = User(email=email, password=hashed_password)
    # add user to USERS
    USERS.update({email: new_user})

    # return response with session cookie and redirect to index
    session_cookie = auth_service.generate_session_token()
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
    password: Annotated[str, Form()]
    ):
    """Sign in a user"""
    # check if user exists
    db_user: User = USERS.get(email)
    if not db_user:
        return templates.TemplateResponse(
            request=request,
            name="/auth/form-error.html",
            context={"request": request, "error": "Invalid email or password."}
            
        )
    # verify the password
    if not auth_service.verify_password(password, db_user.password):
        return templates.TemplateResponse(
            request=request,
            name="/auth/form-error.html",
            context={"request": request, "error": "Invalid email or password"}
            
        )

    # return response with session cookie and redirect to index
    session_cookie = auth_service.generate_session_token()
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
def signout(request: Request, response: Response):
    """Sign out a user"""
    response = Response(status_code=200)
    response.delete_cookie(key="session-id")
    response.headers["HX-Redirect"] = "/signin"
    return response