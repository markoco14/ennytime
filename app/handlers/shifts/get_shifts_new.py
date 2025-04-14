
from fastapi import Request
from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session

from app.core.template_utils import templates
from app.models.user_model import DBUser
from app.services import chat_service


def handle_get_shifts_new(request: Request, current_user: DBUser, db: Session):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response
    
    user_chat_data = chat_service.get_user_chat_data(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "chat_data": user_chat_data
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