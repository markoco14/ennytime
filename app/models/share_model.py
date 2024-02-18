
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from app.core.database import Base  # Make sure this import points to your Base declarative base instance

# change type to name later, easier to understand in the app


class DbShare(Base):
    """Model for the shares table"""
    __tablename__ = "etime_shares"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True, nullable=False)
    guest_id = Column(Integer, index=True, nullable=False)

    # Define the unique constraint within the table metadata
    __table_args__ = (
        UniqueConstraint('owner_id', 'guest_id', name='uix_owner_id_guest_id'),
    )