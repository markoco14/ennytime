""" Service to handle chat related operations. """

import logging
import time
from sqlalchemy.orm import Session
from app.models.chat_models import DBChatRoom, DBChatMessage


def get_user_unread_message_count(db: Session, current_user_id: int):
    """ Returns a list of unread messages for the current user. """
    db_chat_room = db.query(DBChatRoom).filter(
        DBChatRoom.is_active == 1,
        DBChatRoom.chat_users.contains(current_user_id)
    ).first()

    if not db_chat_room:
        return 0

    db_chat_messages = db.query(DBChatMessage).filter(
        DBChatMessage.room_id == db_chat_room.room_id,
        DBChatMessage.is_read == 0,
        DBChatMessage.sender_id != current_user_id
    ).all()

    return len(db_chat_messages)


def get_user_chat_data(db: Session, current_user_id: int):
    """ Returns a list of unread messages for the current user. """
    chat_room_query_start = time.perf_counter()
    db_chat_room = db.query(DBChatRoom).filter(
        DBChatRoom.is_active == 1,
        DBChatRoom.chat_users.contains(current_user_id)
    ).first()
    chat_room_query_end = time.perf_counter()
    chat_room_query_time = chat_room_query_end - chat_room_query_start

    if not db_chat_room:
        return None
    
    chat_unread_messages_query_start = time.perf_counter()
    db_chat_messages = db.query(DBChatMessage).filter(
        DBChatMessage.room_id == db_chat_room.room_id,
        DBChatMessage.is_read == 0,
        DBChatMessage.sender_id != current_user_id
    ).all()
    chat_unread_messages_query_end = time.perf_counter()
    chat_unread_messages_query_time = chat_unread_messages_query_end - chat_unread_messages_query_start

    logging.info(f"Total time for chat room query is {chat_room_query_time} seconds.")
    logging.info(f"Total time for chat unread messages query is {chat_unread_messages_query_time} seconds.")
    logging.info(f"Total time for all chat data queries is {chat_unread_messages_query_time + chat_room_query_time} seconds.")

    return {
        "chatroom_id": db_chat_room.room_id,
        "unread_messages": len(db_chat_messages)
        }
