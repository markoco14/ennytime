""" Service to handle chat related operations. """
import logging
from sqlalchemy.orm import Session

from pydantic import BaseModel

from app.queries import chat_queries

class ChatData(BaseModel):
    chatroom_id: str
    unread_messages: int


def get_user_chat_data(db: Session, current_user_id: int):
    """
    Returns a list of unread messages for the current user.
    If user has no chat rooms at all, returns None.
    If user has no active chat rooms, returns None,
    If user has an active chat room but no unread messages, returns (chatroom_id="some-string", unread_messages=0).
    If user has an active chat room and unread messages, returns (chatroom_id="some-string", unread_messages=some-integer).
    """
    db_chat_data = chat_queries.get_chatroom_id_with_unread_count(db, current_user_id)

    if not db_chat_data:
        logging.info(f"No chat room or messages were found for user {current_user_id}.")
        return None
    
    logging.info(f"Found chat room {db_chat_data[0]} with {db_chat_data[1]} unread messages for user {current_user_id}.")

    return ChatData(
        chatroom_id=db_chat_data[0],
        unread_messages=db_chat_data[1]
    )

def download_chat_data(db: Session, current_user_id: int, room_id: int):
    """ Returns a list of messages for the chatroom. """
    return chat_queries.list_chatroom_messages(db=db, current_user_id=current_user_id, room_id=room_id)
