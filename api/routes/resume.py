from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Dict

from config.database import get_db
from schemas.candidate import CandidateResponse, CandidateCreate
from services.candidate_service import create_candidate
from utils.ai_resume_analyzer import AIResumeAnalyzer

router = APIRouter(prefix="/analyze", tags=["Resume Analysis"])

analyzer = AIResumeAnalyzer()
logger = logging.getLogger(__name__)


@router.post("/", response_model=Dict)
async def analyze_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Resume upload karega, analyze karega aur database mein save karega
    """
    try:
        # File type check
        if not file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are allowed")

        # Text extraction
        if file.filename.lower().endswith('.pdf'):
            resume_text = analyzer.extract_text_from_pdf(file.file)
        else:
            resume_text = analyzer.extract_text_from_docx(file.file)

        if not resume_text or len(resume_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Could not extract text from the resume. Please upload a clear PDF/DOCX.")

        # Structured Data Extraction
        structured_data = analyzer.extract_structured_data(resume_text)

        if "error" in structured_data:
            raise HTTPException(status_code=500, detail=f"AI Extraction failed: {structured_data['error']}")

        # Full Analysis (optional - agar chahiye toh uncomment kar sakte ho)
        # full_analysis = analyzer.analyze_resume(resume_text)

        # Save to Database
        saved_candidate = create_candidate(
            db=db,
            parsed_data=structured_data,
            raw_file_path=file.filename,
            ats_score=structured_data.get("ats_score")
        )

        return {
            "success": True,
            "message": "Resume analyzed and saved successfully",
            "candidate_id": str(saved_candidate.id),
            "full_name": saved_candidate.full_name,
            "job_role": saved_candidate.job_role,
            "ats_score": saved_candidate.ats_score,
            "structured_data": structured_data
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in analyze_resume: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")