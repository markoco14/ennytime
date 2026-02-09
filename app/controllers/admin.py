""" Admin routes """
from datetime import datetime, timedelta
import sqlite3

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import requires_admin
from app.models.user_sign_in import UserSignIn

router = APIRouter(
    prefix="/admin",
    tags=["admin"],

)

templates = Jinja2Templates(directory="templates")


def index(
    request: Request,
    current_user=Depends(requires_admin)
):
    """Returns admin section home page"""
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    return templates.TemplateResponse(
        request=request,
        name="admin/admin-home.html",
        context={
            "current_user": current_user,
        }
    )


def users(
    request: Request,
    current_user=Depends(requires_admin)
):
    """List users"""
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response
    
    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, display_name, email, username FROM users;")
        rows = cursor.fetchall()

    headings = ["Display name", "Email", "Username", "Actions"]

    context = {
        "current_user": current_user,
        "request": request,
        "users": rows,
        "headings": headings,
    }

    return templates.TemplateResponse(
        request=request,
        name="admin/users.html",
        context=context
    )


def signins(
    request: Request,
    current_user=Depends(requires_admin)
):
    """List users"""
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")
        return response

    with sqlite3.connect("db.sqlite3") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
                       SELECT 
                        signins.id as id,
                        signins.created_at as created_at,
                        signins.status as status,
                        users.id as user_id,
                        users.display_name as display_name
                       FROM user_signins as signins 
                       JOIN users ON users.id = signins.user_id 
                       ORDER BY signins.created_at DESC;
                       """)
        user_sign_ins = [UserSignIn(**row) for row in cursor.fetchall()]

    signin_rows = []
    for sign_in in user_sign_ins:
        sign_in.created_at = datetime.strptime(sign_in.created_at, "%Y-%m-%d %H:%M:%S") + timedelta(hours=8)
        signin_rows.append(sign_in)

    context = {
        "current_user": current_user,
        "signins": signin_rows,
    }

    return templates.TemplateResponse(
        request=request,
        name="admin/user-signins.html",
        context=context
    )
