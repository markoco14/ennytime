
from typing import Annotated

from fastapi import APIRouter, Depends,  Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth import auth_service
from app.core.database import get_db


router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/chat", response_class=HTMLResponse)
def get_add_shifts_page(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
):
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)


    context = {
        "request": request,
        "user_data": current_user,
    }

    return block_templates.TemplateResponse(
        name="chat/chat.html",
        context=context
    )

