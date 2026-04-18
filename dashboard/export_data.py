"""Export resume database to Excel / CSV / JSON (no Streamlit)."""

from __future__ import annotations

import io

import pandas as pd

from config.database import get_database_connection

_EXPORT_QUERY = """
    SELECT
        rd.name, rd.email, rd.phone, rd.linkedin, rd.github, rd.portfolio,
        rd.summary, rd.target_role, rd.target_category,
        rd.education, rd.experience, rd.projects, rd.skills,
        ra.ats_score, ra.keyword_match_score, ra.format_score, ra.section_score,
        ra.missing_skills, ra.recommendations,
        rd.created_at
    FROM resume_data rd
    LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
"""


def export_resumes_excel_bytes() -> bytes | None:
    conn = get_database_connection()
    try:
        df = pd.read_sql_query(_EXPORT_QUERY, conn)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Resume Data", index=False)
        buf.seek(0)
        return buf.getvalue()
    except Exception:
        return None
    finally:
        conn.close()


def export_resumes_csv_bytes() -> bytes | None:
    conn = get_database_connection()
    try:
        df = pd.read_sql_query(_EXPORT_QUERY, conn)
        return df.to_csv(index=False).encode("utf-8")
    except Exception:
        return None
    finally:
        conn.close()


def export_resumes_json_str() -> str | None:
    conn = get_database_connection()
    try:
        df = pd.read_sql_query(_EXPORT_QUERY, conn)
        return df.to_json(orient="records", date_format="iso")
    except Exception:
        return None
    finally:
        conn.close()
