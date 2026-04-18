"""Aggregate dashboard statistics for the FastAPI ``/dashboard/metrics`` endpoint."""

from __future__ import annotations

from typing import Any

from config.database import get_ai_analysis_stats, get_resume_stats
from dashboard.queries import (
    get_database_stats,
    get_job_category_stats,
    get_quick_stats,
    get_resume_metrics,
    get_skill_distribution,
    get_weekly_trends,
)


def collect_dashboard_metrics() -> dict[str, Any]:
    """
    Same underlying data as the former Streamlit dashboard / DashboardManager charts,
    in JSON-serializable form.
    """
    cats, counts = get_skill_distribution()
    wdates, wsubs = get_weekly_trends()
    jcats, jsrates = get_job_category_stats()
    return {
        "resume_metrics": get_resume_metrics(),
        "skill_distribution": {"categories": cats, "counts": counts},
        "weekly_trends": {"date_labels": wdates, "submissions": wsubs},
        "job_category_stats": {"categories": jcats, "success_rates": jsrates},
        "database_stats": get_database_stats(),
        "quick_stats": get_quick_stats(),
        "ai_analysis": get_ai_analysis_stats(),
        "resume_overview": get_resume_stats(),
    }
