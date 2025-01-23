""" Service to handle chat related operations. """
from sqlalchemy.orm import Session

from app.queries import chat_queries


def get_user_chat_data(db: Session, current_user_id: int):
    """ Returns a list of unread messages for the current user. """
    return chat_queries.get_chatroom_id_with_unread(db, current_user_id)

def download_chat_data(db: Session, current_user_id: int, room_id: int):
    """ Returns a list of messages for the chatroom. """
    return chat_queries.list_chatroom_messages(db=db, current_user_id=current_user_id, room_id=room_id)
