from typing import Annotated, List
from fastapi import APIRouter, Form, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from auth import auth_service

router = APIRouter()

class User(BaseModel):
    """User"""
    email: str
    password: str

USERS = {
    "johndoe@example.com": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice@example.com": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
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
    # TODO: Check if email is already in use

    # TODO: return response about email/password combo being no good
    
    # Hash password
    hashed_password = auth_service.get_password_hash(password)
    
    # create new user with encrypted password
    user = User(email=email, password=hashed_password)
    # add user to USERS
    USERS.update({email: user})
    print(USERS)

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
def signin(request: Request, response: Response):
    """Sign in a user"""
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
    response.headers["HX-Redirect"] = "/"
    return response