import logging
import time

from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat_models import DBChatMessage, DBChatRoom

class ChatData(BaseModel):
    chatroom_id: str
    unread_messages: int

def get_chatroom_id_with_unread(db: Session, current_user_id: int):
    """
    Returns a ChatData object with a chatroom id (string) and a count of unread messages (int).
    """
    chat_data_query_start = time.perf_counter()
    db_chat_data = db.query(
                        DBChatRoom.room_id,
                        DBChatRoom.chat_users,
                        func.count(DBChatMessage.id).label("message_count")
                    ).outerjoin(
                        DBChatMessage,
                        (DBChatRoom.room_id == DBChatMessage.room_id) &
                        (DBChatMessage.is_read == 0) &
                        (DBChatMessage.sender_id != current_user_id)
                    ).filter(
                        DBChatRoom.is_active == 1,
                        DBChatRoom.chat_users.contains(current_user_id),
                    ).group_by(DBChatRoom.room_id, DBChatRoom.chat_users
                    ).first()
    chat_data_query_time = time.perf_counter() - chat_data_query_start
    logging.info(f"Total time for chat room query is {chat_data_query_time} seconds.")

    if not db_chat_data:
        logging.info(f"No chat room or messages were found for user {current_user_id}.")
        return None
    
    logging.info(f"Found chat room {db_chat_data[0]} with {db_chat_data[2]} unread messages for user {current_user_id}.")
    logging.info(f"Chat room users: {db_chat_data[1]}")
    logging.info(f"type of chat users: {type(db_chat_data[1])}")
    
    for id in db_chat_data[1]:
        logging.info(f"User: {id}")
        logging.info(f"type of user: {type(id)}")
    
    return ChatData(
        chatroom_id=db_chat_data[0],
        unread_messages=db_chat_data[2]
    )

def list_chatroom_messages(db: Session, current_user_id: int, room_id: int):
    """
    Downloads all of the messages from the user's chatroom.
    """
    db_chat_messages = db.query(DBChatMessage
                                ).join(
                                    DBChatRoom,
                                    DBChatRoom.room_id == DBChatMessage.room_id
                                ).filter(
                                    DBChatRoom.room_id == room_id,
                                    DBChatRoom.chat_users.contains(current_user_id),
                                ).all()
    
    return db_chat_messages