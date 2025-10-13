"""Database model for shift types."""

from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base  # Make sure this import points to your Base declarative base instance

# change type to name later, easier to understand in the app

class DbShift(Base):
    """Database model for shift types."""
    __tablename__ = 'etime_shifts'

    id = Column(Integer, primary_key=True, index=True)
    type_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)

    # If you want to use ORM relationships to automatically fetch the associated user
    # user = relationship("DBUser", back_populates="shift_types") 