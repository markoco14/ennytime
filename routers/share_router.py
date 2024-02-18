
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.auth import auth_service
from core.database import get_db
from repositories import share_repository

from app import schemas

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/share-calendar/{target_user_id}", response_class=HTMLResponse | Response)
def share_calendar(
    request: Request,
    target_user_id: int,
    db: Annotated[Session, Depends(get_db)]
    ):
    """Share calendar page"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="signin.html",
            headers={"HX-Redirect": "/"},
        )

    session_data: Session = auth_service.get_session_data(db=db, session_token=request.cookies.get("session-id"))

    try:
        current_user: schemas.User = auth_service.get_current_user(db=db, user_id=session_data.user_id)
    except AttributeError:
        # TODO: figure out how to specify because may be other errors
        # although this response may just be fine
        # AttributeError: 'NoneType' object has no attribute 'user_id'
        response = templates.TemplateResponse(
        request=request,
        name="signin.html",
        headers={"HX-Redirect": "/signin"},
    )
        response.delete_cookie("session-id")
        return response

    
    new_db_share = schemas.CreateShare(
        owner_id=current_user.id,
        guest_id=target_user_id
    )
    new_db_share = share_repository.create_share(db=db, new_share=new_db_share)

    return templates.TemplateResponse(
        request=request,
        name="success.html",
        context={"request": request, "new_share": new_db_share},
    )