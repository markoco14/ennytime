""" Service to handle chat related operations. """

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
