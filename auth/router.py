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

USERS = {
    "johndoe@example.com": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "password": "fakehashedsecret",
        "disabled": False,
    },
    "alice@example.com": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "password": "fakehashedsecret2",
        "disabled": True,
    },
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
    user = USERS.get(email)
    if user:
        return templates.TemplateResponse(
            request=request,
            name="/auth/form-error.html",
            context={"request": request, "error": "Invalid email or password."}
        )
    # Hash password
    hashed_password = auth_service.get_password_hash(password)
    
    # create new user with encrypted password
    user = User(email=email, password=hashed_password)
    # add user to USERS
    USERS.update({email: user})

    # return response with session cookie and redirect to index
    response = Response(status_code=200)
    response.set_cookie(
        key="session-test",
        value="this-is-a-session-id",
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
    user = USERS.get(email)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="/auth/form-error.html",
            context={"request": request, "error": "Invalid email or password."}
            
        )
    # verify the password
    if not auth_service.verify_password(password, user.password):
        return templates.TemplateResponse(
            request=request,
            name="/auth/form-error.html",
            context={"request": request, "error": "Invalid email or password"}
            
        )

    # return response with session cookie and redirect to index
    response = Response(status_code=200)
    response.set_cookie(
        key="session-test",
        value="this-is-a-session-id",
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
    response.delete_cookie(key="session-test")
    response.headers["HX-Redirect"] = "/signin"
    return response