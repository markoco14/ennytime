"""Database model for shift types."""

from sqlalchemy import Column, Integer, String
from core.database import Base  # Make sure this import points to your Base declarative base instance

# change type to name later, easier to understand in the app

class DbShiftType(Base):
    """Database model for shift types."""
    __tablename__ = 'etime_shift_types'

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(255), nullable=False)
    user_id = Column(Integer, nullable=False)

    # If you want to use ORM relationships to automatically fetch the associated user
    # user = relationship("DBUser", back_populates="shift_types") 
