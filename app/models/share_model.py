
from sqlalchemy import Column, Integer
# Make sure this import points to your Base declarative base instance
from app.core.database import Base

# change type to name later, easier to understand in the app


class DbShare(Base):
    """
    Model for the shares table
    sender_id: the user who is giving access to their calendar
        the sender_id is unique because a user can only share their calendar
        with one user at a time
    receiver_id: the user who is receiving access to a user's calendar
        the receiver_id is unique because a user can only receive one calendar from one other user at a time
    In this way, one user can appear as sender_id only once, and as a receiver_id only once, and they can appear a maximum of two times in the table.
    """
    __tablename__ = "etime_shares"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, index=True, nullable=False, unique=True)
    receiver_id = Column(Integer, index=True, nullable=False, unique=True)
