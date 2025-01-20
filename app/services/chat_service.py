""" Service to handle chat related operations. """
from sqlalchemy.orm import Session

from app.queries import chat_queries


def get_user_chat_data(db: Session, current_user_id: int):
    """ Returns a list of unread messages for the current user. """
    db_chat_data = chat_queries.get_chatroom_id_with_unread(db, current_user_id)
    return db_chat_data


