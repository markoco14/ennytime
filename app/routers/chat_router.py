
from typing import Annotated

from fastapi import APIRouter, Depends, Form,  Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.auth import auth_service
from app.core.database import get_db
from app.repositories import share_repository

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")

CHATS = []

MESSAGES = [
    {
        "message": "Hey there! How are you doing today?",
        "time": "3:45 PM",
        "sender_id": 30,
        "recipient_id": 31,
    },
    {
        "message": "I'm doing great, thanks for asking!",
        "time": "3:46 PM",
        "sender_id": 31,
        "recipient_id": 30,
    },
    {
        "message": "Awesome, I'm glad to hear that. Do you have any plans for the weekend?",
        "time": "3:47 PM",
        "sender_id": 30,
        "recipient_id": 31,
    },
    {
        "message": "I'm actually going to the beach with some friends. Should be a lot of fun!",
        "time": "3:48 PM",
        "sender_id": 31,
        "recipient_id": 30,
    },
    {
        "message": "Oooh, sounds like a blast! I hope you have a great time.",
        "time": "3:49 PM",
        "sender_id": 30,
        "recipient_id": 31,
    },
    {
        "message": "Thanks! What are your plans?",
        "time": "3:49 PM",
        "sender_id": 31,
        "recipient_id": 30,
    },
    {
        "message": "I'm going hiking with my family. Pretty excited, but also kind of dreading it!",
        "time": "3:50 PM",
        "sender_id": 30,
        "recipient_id": 31,
    },
    {
        "message": "That sounds amazing! I hope you have a wonderful time.",
        "time": "3:51 PM",
        "sender_id": 31,
        "recipient_id": 30,
    },
    {
        "message": "Thank you! I'm sure it will be a lot of fun.",
        "time": "3:52 PM",
        "sender_id": 30,
        "recipient_id": 31,
    },
    {
        "message": "other chat a",
        "time": "3:51 PM",
        "sender_id": 64,
        "recipient_id": 65,
    },
    {
        "message": "other chat b",
        "time": "3:52 PM",
        "sender_id": 65,
        "recipient_id": 64,
    },
    {
        "message": "other chat a",
        "time": "3:51 PM",
        "sender_id": 64,
        "recipient_id": 65,
    },
    {
        "message": "other chat b",
        "time": "3:52 PM",
        "sender_id": 65,
        "recipient_id": 64,
    },
    {
        "message": "other chat a",
        "time": "3:51 PM",
        "sender_id": 64,
        "recipient_id": 65,
    },
    {
        "message": "other chat b",
        "time": "3:52 PM",
        "sender_id": 65,
        "recipient_id": 64,
    },
    {
        "message": "other chat a",
        "time": "3:51 PM",
        "sender_id": 64,
        "recipient_id": 65,
    },
    {
        "message": "other chat b",
        "time": "3:52 PM",
        "sender_id": 65,
        "recipient_id": 64,
    },
]


@router.get("/chat", response_class=HTMLResponse)
def get_chat(
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

    # we get the current user from the request cookie
    # we get the share id from the current user's shares
    # but maybe we don't need the share ID
    # we get the current user's current chat and all related messages
    # even if they are the other user

    chats = CHATS
    share = share_repository.get_share_by_owner_id(
        db=db, user_id=current_user.id)

    context = {
        "request": request,
        "user_data": current_user,
        "chats": chats,
        "share": share,
    }

    return block_templates.TemplateResponse(
        name="chat/chat.html",
        context=context
    )


@router.get("/chat/{chat_id}", response_class=HTMLResponse)
def get_user_chat(
    request: Request,
    chat_id: int,
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
    
    print("chat id", chat_id)

    # we get the current user from the request cookie
    # we get the share id from the current user's shares
    # but maybe we don't need the share ID
    # we get the current user's current chat and all related messages
    # even if they are the other user

    related_messages = []
    for message in MESSAGES:
        if message["sender_id"] == current_user.id or message["recipient_id"] == current_user.id:
            related_messages.append(message)

    context = {
        "request": request,
        "user_data": current_user,
        "messages": related_messages
        # "chats": chats,
        # "shares": shares,
    }

    return block_templates.TemplateResponse(
        name="chat/chat_room.html",
        context=context
    )

@router.post("/chat/{chat_id}", response_class=HTMLResponse)
def post_new_message(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    message: Annotated[str, Form()]
):
    """
    Add a new message to the chat
    """
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )

    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)

    MESSAGES.append({
        "message": message,
        "time": "3:52 PM",
        "sender_id": current_user.id
    })

    return Response(status_code=200)
