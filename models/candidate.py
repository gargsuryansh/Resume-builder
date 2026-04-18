from sqlalchemy import Column, String, Float, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func
import uuid
from config.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20))
    location = Column(String(100), index=True)
    job_role = Column(String(100), nullable=False, index=True)
    
    total_experience = Column(Float)                    # in years
    skills = Column(ARRAY(String))                      # Example: ["Python", "FastAPI", "AWS"]
    
    education = Column(JSON)
    experience = Column(JSON)
    projects = Column(JSON)
    
    raw_file_path = Column(Text)
    ats_score = Column(Float)
    ai_analysis = Column(JSON)          # strengths, weaknesses, summary, suggestions
    parsed_data = Column(JSON)          # complete AI extracted data
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
