from sqlalchemy.orm import Session
from models.candidate import Candidate
from typing import Dict, Any, List

def create_candidate(db: Session, parsed_data: Dict[str, Any], raw_file_path: str = None, ats_score: float = None) -> Candidate:
    """
    Maps AI extracted data to the Candidate model and saves it to PostgreSQL.
    """
    
    # Extract data from parsed_data with fallbacks
    # Assuming parsed_data follows the structured format from Gemini
    
    new_candidate = Candidate(
        full_name=parsed_data.get("full_name", "N/A"),
        email=parsed_data.get("email"),
        phone=parsed_data.get("phone"),
        location=parsed_data.get("location"),
        job_role=parsed_data.get("job_role", "Unknown"),
        total_experience=float(parsed_data.get("total_experience", 0.0)),
        skills=parsed_data.get("skills", []),
        
        education=parsed_data.get("education", []),
        experience=parsed_data.get("experience", []),
        projects=parsed_data.get("projects", []),
        
        raw_file_path=raw_file_path,
        ats_score=ats_score,
        
        # Storing the full structured response for future reference
        ai_analysis={
            "summary": parsed_data.get("summary", ""),
            "strengths": parsed_data.get("strengths", []),
            "weaknesses": parsed_data.get("weaknesses", []),
            "suggestions": parsed_data.get("suggestions", [])
        },
        parsed_data=parsed_data
    )
    
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    
    return new_candidate

def search_candidates(db: Session, filters: Dict[str, Any], limit: int = 50, offset: int = 0) -> List[Candidate]:
    """
    Advanced candidate search with dynamic filters for HR dashboard.
    """
    query = db.query(Candidate)

    # 1. Job Role Filter (ILike for fuzzy matching)
    if filters.get("job_role"):
        query = query.filter(Candidate.job_role.ilike(f"%{filters['job_role']}%"))

    # 2. Experience Filter
    if filters.get("min_experience") is not None:
        query = query.filter(Candidate.total_experience >= filters["min_experience"])

    # 3. Location Filter (ILike)
    if filters.get("location"):
        query = query.filter(Candidate.location.ilike(f"%{filters['location']}%"))

    # 4. ATS Score Filter
    if filters.get("min_ats_score") is not None:
        query = query.filter(Candidate.ats_score >= filters["min_ats_score"])

    # 5. Skills Filter (PostgreSQL ARRAY overlap)
    # Checks if the candidate has ANY of the requested skills
    if filters.get("skills"):
        query = query.filter(Candidate.skills.overlap(filters["skills"]))

    # 6. Sorting Logic
    sort_by = filters.get("sort_by", "ats_score")
    order = filters.get("order", "desc")
    
    sort_column = getattr(Candidate, sort_by, Candidate.ats_score)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # 7. Pagination
    return query.offset(offset).limit(limit).all()

def get_candidate_by_id(db: Session, candidate_id: str):
    return db.query(Candidate).filter(Candidate.id == candidate_id).first()

def get_all_candidates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Candidate).offset(skip).limit(limit).all()
