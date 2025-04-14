
from fastapi import Request
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session

from app.core.template_utils import templates
from app.models.user_model import DBUser
from app.repositories import shift_type_repository
from app.services import chat_service


def handle_get_shifts_page(request: Request, current_user: DBUser, db: Session):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response
    
    shift_types = shift_type_repository.list_user_shift_types(
        db=db, user_id=current_user.id)
    if not shift_types:
        response = RedirectResponse(status_code=303, url="/shifts/setup") 
        return response
    
    # get chatroom id to link directly from the chat icon
    # get unread message count so chat icon can display the count on page load
    user_chat_data = chat_service.get_user_chat_data(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "chat_data": user_chat_data,
        "shift_types": shift_types
    }
    
    if request.headers.get("HX-Request"):
        response = templates.TemplateResponse(
            name="/shifts/partials/list.html",
            context=context
        )

        return response


    response = templates.TemplateResponse(
        name="/shifts/index.html",
        context=context
    )

    return response