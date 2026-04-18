"""Dashboard data access (headless; no Streamlit)."""

from dashboard.export_data import (
    export_resumes_csv_bytes,
    export_resumes_excel_bytes,
    export_resumes_json_str,
)
from dashboard.queries import (
    get_database_stats,
    get_job_category_stats,
    get_quick_stats,
    get_resume_metrics,
    get_skill_distribution,
    get_weekly_trends,
)

__all__ = [
    "export_resumes_csv_bytes",
    "export_resumes_excel_bytes",
    "export_resumes_json_str",
    "get_database_stats",
    "get_job_category_stats",
    "get_quick_stats",
    "get_resume_metrics",
    "get_skill_distribution",
    "get_weekly_trends",
]
