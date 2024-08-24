""" Admin routes """
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db

from app.repositories import user_repository as UserRepository
from app.services import chat_service

router = APIRouter(
    prefix="/admin",
    tags=["admin"],

)
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse | RedirectResponse)
def read_admin_home_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency)
):
    """Returns admin section home page"""
    if not current_user:
        response = RedirectResponse(url="/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if not current_user.is_admin:
        response = RedirectResponse(url="/")
        return response

    # get unread message count so chat icon can display the count on page load
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "current_user": current_user,
        "request": request,
        "message_count": message_count
    }

    return templates.TemplateResponse(
        request=request,
        name="admin/admin-home.html",
        context=context
    )


@router.get("/users", response_class=HTMLResponse)
def list_users(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency)
):
    """List users"""
    if not current_user:
        response = RedirectResponse(url="/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if not current_user.is_admin:
        response = RedirectResponse(url="/")
        return response

    users = UserRepository.list_users(db=db)
    headings = ["Display name", "Email", "Username", "Actions"]

    # get unread message count so chat icon can display the count on page load
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "current_user": current_user,
        "request": request,
        "users": users,
        "headings": headings,
        "message_count": message_count
    }

    return templates.TemplateResponse(
        request=request,
        name="admin/users.html",
        context=context
    )


@router.delete("/users/{user_id}", response_class=JSONResponse)
def delete_user(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency)
):
    if not current_user:
        response = RedirectResponse(url="/signin")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    if not current_user.is_admin:
        response = JSONResponse(status_code=401, content="Unauthorized")
        return response

    db_user = UserRepository.get_user_by_id(
        db=db, user_id=user_id)

    db.delete(db_user)
    db.commit()

    return Response(status_code=200)

# @router.get("/sessions", response_class=HTMLResponse)
# def list_sessions(
#     request: Request,
#     db: Annotated[Session, Depends(get_db)],
#     current_user = Depends(auth_service.get_current_user)

#     ):
#     """List sessions"""
#    if not current_user:
    #   response = RedirectResponse(url="/signin")
    #    if request.cookies.get("session-id"):
    #         response.delete_cookie("session-id")
    #     return response

    # if not current_user.is_admin:
    #     response = RedirectResponse(url="/")
    #     return response

#     sessions = session_repository.list_sessions(db=db)
#     headings = ["ID", "Session Token", "User ID", "Expiry date", "Actions"]
#     context = {
#         "request": request,
#     "sessions": sessions,
#     "headings": headings
#     }
#     return templates.TemplateResponse(
#         request=request,
#         name="admin/sessions.html",
#         context=context
#     )
