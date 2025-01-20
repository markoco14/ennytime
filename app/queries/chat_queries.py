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
                        func.count(DBChatMessage.id).label("message_count")
                    ).outerjoin(
                        DBChatMessage,
                        (DBChatRoom.room_id == DBChatMessage.room_id) &
                        (DBChatMessage.is_read == 0) &
                        (DBChatMessage.sender_id != current_user_id)
                    ).filter(
                        DBChatRoom.is_active == 1,
                        DBChatRoom.chat_users.contains(current_user_id),
                    ).group_by(DBChatRoom.room_id
                    ).first()
    chat_data_query_time = time.perf_counter() - chat_data_query_start

    logging.info(f"Total time for chat room query is {chat_data_query_time} seconds.")
    
    if not db_chat_data:
        return None
    
    return ChatData(
        chatroom_id=db_chat_data[0],
        unread_messages=db_chat_data[1]
    )
