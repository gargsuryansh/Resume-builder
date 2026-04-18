from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from config.database import Base

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=True) # Optional link to user
    full_name = Column(String(100))
    email = Column(String(100))
    rating = Column(Integer) # 1 to 5
    message = Column(Text)
    category = Column(String(50), default="General") # Feature, Bug, General
    created_at = Column(DateTime(timezone=True), server_default=func.now())
