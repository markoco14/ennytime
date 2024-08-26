
from typing import Annotated
from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.auth import auth_service
from app.core.database import get_db
from app.repositories import share_repository, user_repository

from app.schemas import schemas

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/share-calendar/{target_user_id}", response_class=HTMLResponse | Response)
def share_calendar(
    request: Request,
    target_user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency)
):
    """Share calendar page"""
    if not current_user:
        response = JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
            headers={"HX-Trigger": 'unauthorizedRedirect'}
        )
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")

        return response
    # TODO: would this be more secure if it sent owner ID also?
    # then we could check if the owner ID mathces the current user
    # and prevent weird shares?

    new_db_share = schemas.CreateShare(
        sender_id=current_user.id,
        receiver_id=target_user_id
    )
    new_db_share = share_repository.create_share(db=db, new_share=new_db_share)
    share_user = user_repository.get_user_by_id(
        db=db, user_id=new_db_share.receiver_id)
    return templates.TemplateResponse(
        request=request,
        name="profile/shares/calendar-is-shared.html",
        context={
            "request": request,
            "share": new_db_share,
            "share_user": share_user,
            "current_user_sched_receiver": share_user,
            "message": "Calendar shared!"
        },
    )


@router.delete("/share-calendar/{share_id}", response_class=HTMLResponse)
def unshare(request: Request, db: Annotated[Session, Depends(get_db)], share_id: int):
    """Unshare calendar page"""
    # return "Unshared"
    try:
        share_repository.delete_share(db=db, share_id=share_id)
    except IntegrityError:
        return "IntegrityError"
    return templates.TemplateResponse(
        request=request,
        name="profile/shares/calendar-not-shared.html",
        context={
            "request": request,
            "message": "Calendar unshared!"
        },
    )
