from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from jobs.linkedin_scraper import LinkedInScraper
from api.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/jobs", tags=["Job Search"])

class JobSearchRequest(BaseModel):
    job_titles: List[str]
    location: str = "India"
    count: int = 5

@router.post("/search")
def search_jobs(
    request: JobSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Search for jobs on LinkedIn using Selenium scraper.
    """
    try:
        results = LinkedInScraper.search_jobs_headless(
            job_title_input=request.job_titles,
            job_location=request.location,
            job_count=request.count
        )
        
        if "error" in results:
            raise HTTPException(status_code=500, detail=results["error"])
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
