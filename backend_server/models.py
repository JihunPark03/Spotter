from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from db_init import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    is_ad = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
