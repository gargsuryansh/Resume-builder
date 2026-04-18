from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class CandidateBase(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    job_role: str
    total_experience: Optional[float] = None
    skills: List[str] = []
    
    education: List[Dict[str, Any]] = []
    experience: List[Dict[str, Any]] = []
    projects: List[Dict[str, Any]] = []
    
class CandidateCreate(CandidateBase):
    raw_file_path: Optional[str] = None
    ats_score: Optional[float] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    parsed_data: Optional[Dict[str, Any]] = None

class CandidateFilter(BaseModel):
    job_role: Optional[str] = None
    min_experience: Optional[float] = None
    location: Optional[str] = None
    skills: Optional[List[str]] = None
    min_ats_score: Optional[float] = None
    sort_by: Optional[str] = "ats_score" # "ats_score" or "experience"
    order: Optional[str] = "desc" # "asc" or "desc"

class CandidateResponse(CandidateBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
