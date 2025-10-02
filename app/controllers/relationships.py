from collections import namedtuple

from typing import Annotated
from fastapi import APIRouter, Depends, Form, Request, Response
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


def share(
    request: Request,
    receiver_id: int,
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
        receiver_id=receiver_id
    )
    try:
        new_db_share = share_repository.create_share(
            db=db, new_share=new_db_share)
    except IntegrityError as error:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Someone is already sharing their calendar with this user."}
        )

    share_user = user_repository.get_user_by_id(
        db=db, user_id=new_db_share.receiver_id)
    # to match the named tuple formatting from the /profile page request
    share_with_user_tuple = (new_db_share, share_user)
    current_user_sent_share = namedtuple(
        'ShareWithUser', ['share', 'user'])(*share_with_user_tuple)

    return templates.TemplateResponse(
        request=request,
        name="profile/shares/calendar-is-shared.html",
        context={
            "request": request,
            "share": new_db_share,
            "share_user": share_user,
            "current_user_sent_share": current_user_sent_share,
            "message": "Calendar shared!"
        },
    )


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


def reject(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    share_id: int
):
    """Delete the calendar share entity in DB"""
    share_repository.delete_share(db=db, share_id=share_id)

    return templates.TemplateResponse(
        request=request,
        name="profile/shares/calendar-is-received.html",
        context={
            "request": request,
            "message": "Calendar share request rejected."
        },
    )


def search(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    search_username: Annotated[str, Form()] = "",
    current_user=Depends(auth_service.user_dependency)
):
    """ Returns a list of users that match the search string. """
    if not current_user:
        response = templates.TemplateResponse(
            request=request,
            name="website/web-home.html"
        )
        response.delete_cookie("session-id")

        return response

    if search_username == "":
        return templates.TemplateResponse(
            request=request,
            name="profile/search-results.html",
            context={"request": request, "matched_user": ""}
        )

    matched_user = user_repository.get_user_by_username(
        db=db,
        username=search_username
    )

    context = {
        "request": request,
        "matched_user": matched_user
    }

    return templates.TemplateResponse(
        request=request,
        name="profile/search-results.html",
        context=context
    )