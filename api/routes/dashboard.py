from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from config.database import get_db
from api.deps import get_current_hr_user
from models.user import User
from services import analytics_service, export_service
import io

router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard"])

@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """
    Get aggregated analytics for the dashboard charts.
    """
    return {
        "metrics": analytics_service.get_dashboard_stats(db),
        "skills": analytics_service.get_skill_distribution(db),
        "roles": analytics_service.get_job_role_distribution(db),
        "experience": analytics_service.get_experience_distribution(db)
    }

@router.get("/export/csv")
def export_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """
    Download candidates data in CSV format.
    """
    buffer = export_service.export_candidates_to_csv(db)
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=candidates_export.csv"}
    )

@router.get("/export/excel")
def export_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_hr_user)
):
    """
    Download candidates data in Excel format.
    """
    buffer = export_service.export_candidates_to_excel(db)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=candidates_export.xlsx"}
    )
