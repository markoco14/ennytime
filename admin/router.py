""" Admin routes """
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from auth import auth_service

from repositories import user_repository as UserRepository
from repositories import session_repository as SessionRepository

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/users", response_class=HTMLResponse)
def list_users(request: Request):
    """List users"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )
    
    users = UserRepository.list_users()
    context = {
        "request": request,
        "users": users,
    }
    
    return templates.TemplateResponse(
        request=request,
        name="users.html",
        context=context
    )

@router.get("/sessions", response_class=HTMLResponse)
def list_sessions(request: Request):
    """List sessions"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="landing-page.html",
            headers={"HX-Redirect": "/"},
        )
    
    sessions = SessionRepository.list_sessions()
    context = {
        "request": request,
    "sessions": sessions,
    }
    return templates.TemplateResponse(
        request=request,
        name="sessions.html",
        context=context
    )