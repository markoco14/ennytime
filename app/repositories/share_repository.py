
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.models.share_model import DbShare
from app.models.user_model import DBUser
from app.schemas import schemas


def get_user_shares(db: Session, user_id: int):
    """Get all shares of a user"""
    db_shares = db.query(DbShare).filter(
        DbShare.sender_id == user_id).all()
    return db_shares


def get_share_by_sender_id(db: Session, user_id: int):
    """Get a share by user id"""
    db_share = db.query(DbShare).filter(
        DbShare.sender_id == user_id).first()
    return db_share


def get_share_by_receiver_id(db: Session, receiver_id: int):
    """Get a share by guest id"""
    db_share = db.query(DbShare).filter(
        DbShare.receiver_id == receiver_id).first()
    return db_share


def create_share(db: Session, new_share: schemas.CreateShare):
    """Create a share in the database"""
    share = DbShare(**new_share.model_dump())
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


def delete_share(db: Session, share_id: int):
    """Delete a share from the database"""
    db.query(DbShare).filter(DbShare.id == share_id).delete()
    db.commit()


def get_share_user_with_shifts_by_receiver_id(db: Session, share_user_id: int):
    query = text("""
        SELECT 
            etime_users.display_name,
            etime_users.birthday,
            etime_users.id
        FROM etime_users WHERE id = :share_user_id
    """)
    result = db.execute(
        query, {"share_user_id": share_user_id}
    ).fetchone()._asdict()

    return DBUser(**result)
