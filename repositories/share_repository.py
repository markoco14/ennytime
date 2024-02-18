
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from repositories import share_repository
from models.share_model import DbShare
import schemas
from core.database import test_db

def get_share_by_guest_id(db: Session, guest_id: int) -> DbShare:
    """Get a share by guest id"""
    db_share = db.query(DbShare).filter(
        DbShare.guest_id == guest_id).first()
    return db_share

def create_share(db: Session, owner_id: int, guest_id: int) -> DbShare:
    """Create a share in the database"""
    share = DbShare(
        owner_id=owner_id,
        guest_id=guest_id,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    return share


# try:
    
#     test_create_share = schemas.CreateShare(
#         owner_id=1,
#         guest_id=2
#     )
#     create_share(
#         db=test_db,
#         owner_id=test_create_share.owner_id,
#         guest_id=test_create_share.guest_id,
#      )
#     share = get_share_by_guest_id(db=test_db, guest_id=2)
#     print(share)
# except IntegrityError as e:
#     print(e.orig)
# finally:
#     test_db.close()


