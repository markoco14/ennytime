import random
import string
import uuid
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
from app.models.chat_models import DBChatRoom

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")

CHATS = []

MESSAGES = [
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f",
        "message": "Hey there! How are you doing today?",
        "time": "3:45 PM",
        "sender_id": 30,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f",
        "message": "I'm doing great, thanks for asking!",
        "time": "3:46 PM",
        "sender_id": 31,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f",
        "message": "Awesome, I'm glad to hear that. Do you have any plans for the weekend?",
        "time": "3:47 PM",
        "sender_id": 30,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f",
        "message": "I'm actually going to the beach with some friends. Should be a lot of fun!",
        "time": "3:48 PM",
        "sender_id": 31,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f",
        "message": "Oooh, sounds like a blast! I hope you have a great time.",
        "time": "3:49 PM",
        "sender_id": 30,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f",
        "message": "Thanks! What are your plans?",
        "time": "3:49 PM",
        "sender_id": 31,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f",
        "message": "I'm going hiking with my family. Pretty excited, but also kind of dreading it!",
        "time": "3:50 PM",
        "sender_id": 30,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f",
        "message": "That sounds amazing! I hope you have a wonderful time.",
        "time": "3:51 PM",
        "sender_id": 31,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f",
        "message": "Thank you! I'm sure it will be a lot of fun.",
        "time": "3:52 PM",
        "sender_id": 30,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f123",
        "message": "other chat a",
        "time": "3:51 PM",
        "sender_id": 64,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f123",
        "message": "other chat b",
        "time": "3:52 PM",
        "sender_id": 65,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f123",
        "message": "other chat a",
        "time": "3:51 PM",
        "sender_id": 64,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f123",
        "message": "other chat b",
        "time": "3:52 PM",
        "sender_id": 65,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f123",
        "message": "other chat a",
        "time": "3:51 PM",
        "sender_id": 64,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f123",
        "message": "other chat b",
        "time": "3:52 PM",
        "sender_id": 65,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f123",
        "message": "other chat a",
        "time": "3:51 PM",
        "sender_id": 64,
    },
    {
        "room_id": "3f75798b8fe54715b8b85857c148957f123",
        "message": "other chat b",
        "time": "3:52 PM",
        "sender_id": 65,
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

    chat = db.query(DBChatRoom).filter(
        DBChatRoom.is_active == 1,
        DBChatRoom.chat_users.contains(current_user.id)
    ).first()
    # if chat:
    #     print(chat.__dict__)
    share = share_repository.get_share_by_owner_id(
        db=db, user_id=current_user.id)

    context = {
        "request": request,
        "user_data": current_user,
        "chat": chat,
        "share": share,
    }

    return block_templates.TemplateResponse(
        name="chat/chat.html",
        context=context
    )


def generate_room_id():
    """Generate a random room id"""
    length = 16
    characters = string.ascii_letters + string.digits

    return uuid.uuid4().hex
    return ''.join(random.choice(characters) for _ in range(length))


@router.post("/create-chat/{owner_id}/{guest_id}", response_class=HTMLResponse)
def create_new_chat(
    request: Request,
    owner_id: int,
    guest_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    """Create a new chat room for the couple"""
    if not auth_service.get_session_cookie(request.cookies):
        return templates.TemplateResponse(
            request=request,
            name="website/web-home.html",
            headers={"HX-Redirect": "/"},
        )
    current_user = auth_service.get_current_session_user(
        db=db,
        cookies=request.cookies)

    chat_room_id = generate_room_id()
    db_chat = DBChatRoom(
        room_id=chat_room_id,
        chat_users=[owner_id, guest_id]
    )
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)

    return templates.TemplateResponse(
        name="/chat/enter-room-link.html",
        context={
            "request": request,
            "room_id": chat_room_id
        }
    )
    return f"Enter Chat {chat_room_id}"


@router.get("/chat/{room_id}", response_class=HTMLResponse)
def get_user_chat(
    request: Request,
    room_id: str,
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

    print("chat id", room_id)

    # we get the current user from the request cookie
    # we get the share id from the current user's shares
    # but maybe we don't need the share ID
    # we get the current user's current chat and all related messages
    # even if they are the other user

    # we get the chat room and the messages
    # TODO: set up the messages table
    chat_room = db.query(DBChatRoom).filter(
        DBChatRoom.room_id == room_id
    ).first()
    related_messages = []
    for message in MESSAGES:
        if message["room_id"] == room_id:
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
