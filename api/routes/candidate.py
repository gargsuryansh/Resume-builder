from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from config.database import get_db
from schemas.candidate import CandidateResponse, CandidateFilter
from services import candidate_service
from models.user import User
from api.deps import get_current_hr_user

router = APIRouter(prefix="/candidates", tags=["Candidate Management"])

@router.get("/search", response_model=List[CandidateResponse])
def search_candidates(
    job_role: Optional[str] = Query(None),
    min_experience: Optional[float] = Query(None),
    location: Optional[str] = Query(None),
    skills: Optional[str] = Query(None), # Comma separated
    min_ats_score: Optional[float] = Query(None),
    sort_by: str = Query("ats_score"),
    order: str = Query("desc"),
    limit: int = Query(50),
    offset: int = Query(0),
    current_user: User = Depends(get_current_hr_user),
    db: Session = Depends(get_db)
):
    """
    Search and filter candidates for the HR Dashboard.
    """
    
    # Process skills from comma-separated string to list
    skill_list = [s.strip() for s in skills.split(",")] if skills else []
    
    filters = {
        "job_role": job_role,
        "min_experience": min_experience,
        "location": location,
        "skills": skill_list,
        "min_ats_score": min_ats_score,
        "sort_by": sort_by,
        "order": order
    }
    
    candidates = candidate_service.search_candidates(db, filters, limit, offset)
    return candidates
