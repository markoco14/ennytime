
from datetime import timedelta
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2_fragments.fastapi import Jinja2Blocks
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.auth import auth_service
from app.core.database import get_db
from app.core.websocket import websocket_manager
from app.models.chat_models import DBChatRoom, DBChatMessage
from app.models.user_model import DBUser
from app.services import chat_service

router = APIRouter()
templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


@router.get("/chat", response_class=HTMLResponse)
def get_chat(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response

    chat = db.query(DBChatRoom).filter(
        DBChatRoom.is_active == 1,
        DBChatRoom.chat_users.contains(current_user.id)
    ).first()

    query = text("""
        SELECT etime_shares.*,
            etime_users.display_name as guest_first_name
        FROM etime_shares
        LEFT JOIN etime_users ON etime_users.id = etime_shares.receiver_id
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
    return uuid.uuid4().hex


@router.post("/create-chat/{sender_id}/{receiver_id}", response_class=HTMLResponse)
def create_new_chat(
    request: Request,
    sender_id: int,
    receiver_id: int,
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
        chat_users=[sender_id, receiver_id]
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


# WEB SOCKET CHAT BELOW

@router.get("/chat/{room_id}", response_class=HTMLResponse)
def get_chatroom(
    request: Request,
    room_id: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[DBUser, Depends(auth_service.user_dependency)]
):
    if not current_user:
        response = RedirectResponse(status_code=303, url="/")
        response.delete_cookie("session-id")
        return response

    # we get the chat room and the messages
    # TODO: set up the messages table
    chat_room = db.query(DBChatRoom).filter(
        DBChatRoom.room_id == room_id
    ).first()

    messages = db.query(DBChatMessage).filter(
        DBChatMessage.room_id == room_id).all()
    
    for message in messages:
        message.created_at = (message.created_at + timedelta(hours=8)).strftime("%b %d %H:%M")

    context = {
        "request": request,
        "chat": chat_room,
        "current_user": current_user,
        "messages": messages
    }

    return block_templates.TemplateResponse(
        name="chat/chat-room-web-socket.html",
        context=context
    )


@router.websocket("/ws/chat/{room_id}/{user_id}")
async def multi_websocket_endpoint(
    websocket: WebSocket,
    room_id: str,
    user_id: int,
    db: Annotated[Session, Depends(get_db)]
):
    await websocket_manager.connect_chatroom(
        websocket=websocket,
        room_id=room_id,
        user_id=user_id
    )
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)['message']
            db_message = DBChatMessage(
                room_id=room_id,
                message=message,
                sender_id=user_id
            )
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            message_data = {
                "id": db_message.id,
                "sender_id": db_message.sender_id,
                "message": db_message.message,
                "is_read": db_message.is_read,
                "created_at": str((db_message.created_at + timedelta(hours=8)).strftime("%b %d %H:%M"))
            }
            await websocket_manager.broadcast_chatroom(
                message=json.dumps(message_data),
                room_id=room_id
            )
    except WebSocketDisconnect:
        await websocket_manager.disconnect_chatroom(
            websocket=websocket,
            room_id=room_id
        )


@router.get("/read-status/{message_id}", response_class=HTMLResponse)
async def set_message_to_read(
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

    websocket = websocket_manager.find_user_chatroom_connection(
        room_id=db_message.room_id,
        user_id=db_message.sender_id
    )

    message = {
        "message_id": db_message.id,
        "sender_id": db_message.sender_id,
        "is_read": db_message.is_read,
        "read_status_update": True
    }

    if websocket:
        await websocket_manager.send_personal_message(
            message=json.dumps(message),
            websocket=websocket
        )

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
