import re
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import auth_service
from app.core.database import get_db
from app.core.template_utils import templates
from app.dependencies import requires_shift_owner, requires_user
from app.handlers.shifts.delete_shift import handle_delete_shift
from app.handlers.shifts.get_shifts_setup import handle_get_shifts_setup
from app.models.user_model import DBUser
from app.new_models.shift import Shift
from app.repositories import shift_type_repository
from app.viewmodels.structs import ShiftCreate, ShiftRow

router = APIRouter(prefix="/shifts")


def index(
    request: Request,
    current_user=Depends(requires_user),
    ):
    if not current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")
        
    shifts_rows = Shift.get_user_shifts(user_id=current_user.id)

    context = {
        "current_user": current_user,
        "shifts": shifts_rows,
    }
    
    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            request=request,
            name="/shifts/partials/_shifts.html",
            context=context
        )

        return response


    response = templates.TemplateResponse(
        request=request,
        name="/shifts/index.html",
        context=context
    )

    return response


def new(
    request: Request,
    current_user=Depends(requires_user),
    ):
    if not current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")

    context = {
        "request": request,
        "current_user": current_user,
    }

    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="shifts/new/partials/form.html",
            context=context
        )
        return response

    response = templates.TemplateResponse(
        name="shifts/new/index.html",
        context=context
    )
    return response


def create(
    request: Request,
    shift_name: Annotated[str, Form()],
    current_user=Depends(requires_user)
    ):
    if not current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")
    
    # clean up shift name
    cleaned_shift_name = shift_name.strip()
    space_finder_regex = re.compile(r"\s+")
    cleaned_shift_name = re.sub(space_finder_regex, ' ', cleaned_shift_name)
   
    # create short name
    long_name_split = cleaned_shift_name.split(" ")
    short_name = ""
    for part in long_name_split:
        short_name += part[0].upper()

    new_shift = ShiftCreate(
        long_name=shift_name,
        short_name=short_name,
        user_id=current_user[0]
    )

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO shifts (long_name, short_name, user_id) VALUES (?, ?, ?);", (new_shift.long_name, new_shift.short_name, new_shift.user_id))

    if request.headers.get("hx-request"):
        return Response(status_code=200, headers={"hx-redirect": f"/shifts"})
    else:
        return RedirectResponse(status_code=303, url=f"/shifts")


def edit(
    request: Request,
    shift_type_id: int,
    current_user=Depends(requires_shift_owner)
):
    if not current_user:
        if request.headers.get("hx-request"):
            response = Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            response = RedirectResponse(status_code=303, url=f"/signin")
        
        return response
      
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")    
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, long_name, short_name FROM shifts WHERE id = ?", (shift_type_id, ))
            shift = ShiftRow(*cursor.fetchone())
        except Exception as e:
            print(f"no shift found: {e}")
            if request.headers.get("hx-request"):
                return Response(status_code=200, header={"hx-redirect": f"/shifts"})
            else:
                return RedirectResponse(status_code=303, url=f"/shifts")

    response = templates.TemplateResponse(
        name="shifts/edit/index.html",
        context={
            "request": request,
            "shift": shift,
            "current_user": current_user
        }
    )

    return response

async def update(
    request: Request,
    shift_type_id: int,
    current_user=Depends(requires_shift_owner)
):  
    """
    Updates the user's shift. Receives form fields:
        long_name
        short_name
    """
    if not current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")
        
    form_data = await request.form()
    long_name = form_data.get("long_name", None)
    short_name = form_data.get("short_name", None)

    if not long_name or not short_name:
        if request.headers.get("hx-request"):
            return Response(status_code=200, headers={"Hx-Refresh": "true"})
        else:
            return RedirectResponse(status_code=303, url=f"/shifts/{shift_type_id}/edit")
        
    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")    
        cursor = conn.cursor()
        cursor.execute("UPDATE shifts SET long_name=?, short_name=? WHERE id = ?", (long_name, short_name, shift_type_id, ))
        
    if request.headers.get("hx-request"):
        return Response(status_code=200, headers={"Hx-Refresh": "true"})
    else:
        return RedirectResponse(status_code=303, url=f"/shifts/{shift_type_id}/edit")


def delete(
    request: Request,
    shift_type_id: int,
    current_user=Depends(requires_shift_owner)
):
    """Delete shift type"""
    if not current_user:
        if request.headers.get("hx-request"):
            return Response(status_code=200, header={"hx-redirect": f"/signin"})
        else:
            return RedirectResponse(status_code=303, url=f"/signin")
        

    with sqlite3.connect("db.sqlite3") as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM shifts WHERE id = ?", (shift_type_id, ))
        except Exception as e:
            print(f"there was an error deleting shift: {shift_type_id}: {e}")

    return Response(status_code=200)


def setup(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
    ):
    return handle_get_shifts_setup(request, current_user, db)