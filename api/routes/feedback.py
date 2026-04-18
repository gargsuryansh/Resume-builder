from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config.database import get_db
from models.feedback import Feedback
from pydantic import BaseModel, EmailStr
from typing import Optional, List

router = APIRouter(prefix="/feedback", tags=["Feedback System"])

class FeedbackCreate(BaseModel):
    full_name: str
    email: EmailStr
    rating: int
    message: str
    category: Optional[str] = "General"

class FeedbackResponse(FeedbackCreate):
    id: int
    created_at: str
    class Config:
        from_attributes = True

@router.post("/")
def submit_feedback(data: FeedbackCreate, db: Session = Depends(get_db)):
    """
    Submit user feedback/bug report.
    """
    new_fb = Feedback(
        full_name=data.full_name,
        email=data.email,
        rating=data.rating,
        message=data.message,
        category=data.category
    )
    db.add(new_fb)
    db.commit()
    return {"message": "Thank you for your feedback!"}

@router.get("/all")
def get_all_feedback(db: Session = Depends(get_db)):
    """
    Admin only: see all feedback.
    """
    # Note: In production, add @get_current_hr_user protection here
    return db.query(Feedback).order_by(Feedback.created_at.desc()).all()
