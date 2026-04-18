from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from utils.resume_builder import ResumeBuilder
from api.deps import get_current_user
from models.user import User
import io

router = APIRouter(prefix="/builder", tags=["Resume Builder"])
builder = ResumeBuilder()

class PersonalInfo(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    title: Optional[str] = None
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None

class Experience(BaseModel):
    company: str
    position: str
    start_date: str
    end_date: str
    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None

class Project(BaseModel):
    name: str
    technologies: Optional[str] = None
    description: Optional[str] = None
    responsibilities: Optional[List[str]] = None

class Education(BaseModel):
    school: str
    degree: str
    field: str
    graduation_date: str
    gpa: Optional[str] = None

class Skills(BaseModel):
    technical: Optional[List[str]] = None
    soft: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    tools: Optional[List[str]] = None

class ResumeData(BaseModel):
    template: str = "Modern"
    personal_info: PersonalInfo
    summary: Optional[str] = None
    experience: Optional[List[Experience]] = None
    projects: Optional[List[Project]] = None
    education: Optional[List[Education]] = None
    skills: Optional[Skills] = None

@router.post("/generate")
def generate_resume(
    data: ResumeData,
    current_user: User = Depends(get_current_user)
):
    """
    Generate a professional resume DOCX file based on user data and template choice.
    """
    try:
        # Convert Pydantic model to dict
        resume_dict = data.model_dump()
        
        # Generate resume buffer
        buffer = builder.generate_resume(resume_dict)
        
        # Return as streaming response
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=resume_{data.personal_info.full_name.replace(' ', '_')}.docx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
