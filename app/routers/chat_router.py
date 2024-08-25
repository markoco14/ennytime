import string
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form,  Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session
from sqlalchemy.sql import text


from app.auth import auth_service
from app.core.database import get_db
from app.models.chat_models import DBChatRoom, DBChatMessage
from app.services import chat_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


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

    query = text("""
        SELECT etime_shares.*,
            etime_users.display_name as guest_first_name
        FROM etime_shares
        LEFT JOIN etime_users ON etime_users.id = etime_shares.guest_id
        WHERE etime_shares.sender_id = :user_id
    """)
    share_result = db.execute(query, {"user_id": current_user.id}).fetchone()

    # get unread message count so chat icon can display the count on page load
    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "request": request,
        "current_user": current_user,
        "chat": chat,
        "share": share_result,
        "message_count": message_count
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


@router.post("/create-chat/{sender_id}/{guest_id}", response_class=HTMLResponse)
def create_new_chat(
    request: Request,
    sender_id: int,
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
        chat_users=[sender_id, guest_id]
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

    messages = db.query(DBChatMessage).filter(
        DBChatMessage.room_id == room_id).all()
    # print(messages)
    # for message in messages:
    #     print(message)

    context = {
        "request": request,
        "chat": chat_room,
        "current_user": current_user,
        "messages": messages
    }

    return block_templates.TemplateResponse(
        name="chat/chat_room.html",
        context=context
    )


@router.get("/chat/{room_id}/messages", response_class=HTMLResponse)
def get_chat_room_messages(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    room_id: str
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

    messages = db.query(DBChatMessage).filter(
        DBChatMessage.room_id == room_id).all()

    context = {
        "request": request,
        "current_user": current_user,
        "messages": messages
    }

    return block_templates.TemplateResponse(
        name="chat/chat_room.html",
        context=context,
        block_name="messages"
    )


@router.post("/chat/{room_id}", response_class=HTMLResponse)
def post_new_message(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    room_id: str,
    message: Annotated[str, Form()],
    current_user=Depends(auth_service.user_dependency)
):
    """
    Add a new message to the chat
    """
    if not current_user:
        response = JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
            headers={"HX-Trigger": 'unauthorizedRedirect'}
        )
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")

        return response

    db_message = DBChatMessage(
        room_id=room_id,
        message=message,
        sender_id=current_user.id
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    return templates.TemplateResponse(
        name="chat/chat-form.html",
        context={
            "request": request,
            "chat": {
                "room_id": room_id
            }
        }
    )


@router.get("/read-status/{message_id}", response_class=HTMLResponse)
def set_message_to_read(
    request: Request,
    message_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency)
):
    if not current_user:
        response = JSONResponse(
            status_code=401,
            content={"message": "Unauthorized"},
            headers={"HX-Trigger": 'unauthorizedRedirect'}
        )
        if request.cookies.get("session-id"):
            response.delete_cookie("session-id")

        return response

    db_message = db.query(DBChatMessage).filter(
        DBChatMessage.id == message_id).first()

    if not db_message.is_read:
        db_message.is_read = 1
        db.commit()

    return Response(status_code=200)


@router.get("/unread", response_class=HTMLResponse)
def get_unread_messages(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user=Depends(auth_service.user_dependency)
):
    if not current_user:
        context = {
            "current_user": current_user,
            "request": request,
            "message_count": 0
        }

        return block_templates.TemplateResponse(
            name="chat/unread-counter.html",
            context=context
        )

    message_count = chat_service.get_user_unread_message_count(
        db=db,
        current_user_id=current_user.id
    )

    context = {
        "current_user": current_user,
        "request": request,
        "message_count": message_count
    }

    return block_templates.TemplateResponse(
        name="chat/unread-counter.html",
        context=context
    )
