from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.chat_models import DBChatMessage, DBChatRoom, DBChatroomUser

def get_chatroom_id_with_unread_count(db: Session, current_user_id: int):
    """
    Returns a tuple with a chatroom id (string) and a count of unread messages (int).
    """
    db_chat_data = db.query(DBChatRoom.room_id.label("room_id"), func.count(DBChatMessage.id).label("unread_count")
                            ).join(
                                DBChatroomUser,
                                DBChatroomUser.room_id == DBChatRoom.room_id
                            ).outerjoin(
                                DBChatMessage,
                                (DBChatMessage.room_id == DBChatRoom.room_id)
                                & (DBChatMessage.is_read == 0)
                                & (DBChatMessage.sender_id != current_user_id)
                            ).filter(
                                DBChatRoom.is_active == 1,
                                DBChatroomUser.user_id == current_user_id,
                            ).group_by(
                                DBChatRoom.room_id,
                            ).first()
    
    return db_chat_data


def list_chatroom_messages(db: Session, current_user_id: int, room_id: int):
    """
    Downloads all of the messages from the user's chatroom.
    """
    db_chat_messages = db.query(DBChatMessage
                                ).join(
                                    DBChatRoom,
                                    DBChatRoom.room_id == DBChatMessage.room_id
                                ).join(
                                    DBChatroomUser,
                                    DBChatroomUser.room_id == DBChatRoom.room_id
                                ).filter(
                                    DBChatRoom.room_id == room_id,
                                    DBChatroomUser.user_id == current_user_id,
                                ).all()
    
    return db_chat_messages