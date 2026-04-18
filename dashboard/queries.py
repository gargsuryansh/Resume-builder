"""
Dashboard database queries (no Streamlit). Used by FastAPI and any headless consumers.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from config.database import get_database_connection


def get_resume_metrics() -> dict:
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_month = now.replace(day=1)

        metrics: dict = {}
        for period, start_date in [
            ("Today", start_of_day),
            ("This Week", start_of_week),
            ("This Month", start_of_month),
            ("All Time", datetime(2000, 1, 1)),
        ]:
            cursor.execute(
                """
                SELECT
                    COUNT(DISTINCT rd.id) as total_resumes,
                    ROUND(AVG(ra.ats_score), 1) as avg_ats_score,
                    ROUND(AVG(ra.keyword_match_score), 1) as avg_keyword_score,
                    COUNT(DISTINCT CASE WHEN ra.ats_score >= 70 THEN rd.id END) as high_scoring
                FROM resume_data rd
                LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
                WHERE rd.created_at >= ?
            """,
                (start_date.strftime("%Y-%m-%d %H:%M:%S"),),
            )
            row = cursor.fetchone()
            if row:
                metrics[period] = {
                    "total": row[0] or 0,
                    "ats_score": row[1] or 0,
                    "keyword_score": row[2] or 0,
                    "high_scoring": row[3] or 0,
                }
            else:
                metrics[period] = {
                    "total": 0,
                    "ats_score": 0,
                    "keyword_score": 0,
                    "high_scoring": 0,
                }
        return metrics
    finally:
        conn.close()


def get_skill_distribution() -> tuple[list, list]:
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            WITH RECURSIVE split(skill, rest) AS (
                SELECT '', skills || ','
                FROM resume_data
                UNION ALL
                SELECT
                    substr(rest, 0, instr(rest, ',')),
                    substr(rest, instr(rest, ',') + 1)
                FROM split
                WHERE rest <> ''
            ),
            SkillCategories AS (
                SELECT
                    CASE
                        WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%python%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%java%' OR
                             LOWER(TRIM(skill, '[]" ')) LIKE '%javascript%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%c++%' OR
                             LOWER(TRIM(skill, '[]" ')) LIKE '%programming%' THEN 'Programming'
                        WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%sql%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%database%' OR
                             LOWER(TRIM(skill, '[]" ')) LIKE '%mongodb%' THEN 'Database'
                        WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%aws%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%cloud%' OR
                             LOWER(TRIM(skill, '[]" ')) LIKE '%azure%' THEN 'Cloud'
                        WHEN LOWER(TRIM(skill, '[]" ')) LIKE '%agile%' OR LOWER(TRIM(skill, '[]" ')) LIKE '%scrum%' OR
                             LOWER(TRIM(skill, '[]" ')) LIKE '%management%' THEN 'Management'
                        ELSE 'Other'
                    END as category,
                    COUNT(*) as count
                FROM split
                WHERE skill <> ''
                GROUP BY category
            )
            SELECT category, count
            FROM SkillCategories
            ORDER BY count DESC
        """
        )
        categories, counts = [], []
        for row in cursor.fetchall():
            categories.append(row[0])
            counts.append(row[1])
        return categories, counts
    finally:
        conn.close()


def get_weekly_trends() -> tuple[list, list]:
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        now = datetime.now()
        dates = [(now - timedelta(days=x)).strftime("%Y-%m-%d") for x in range(6, -1, -1)]
        submissions = []
        for date in dates:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM resume_data
                WHERE DATE(created_at) = DATE(?)
            """,
                (date,),
            )
            submissions.append(cursor.fetchone()[0])
        return [d[-3:] for d in dates], submissions
    finally:
        conn.close()


def get_job_category_stats() -> tuple[list, list]:
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                COALESCE(target_category, 'Other') as category,
                COUNT(*) as count,
                ROUND(AVG(CASE WHEN ra.ats_score >= 70 THEN 1 ELSE 0 END) * 100, 1) as success_rate
            FROM resume_data rd
            LEFT JOIN resume_analysis ra ON rd.id = ra.resume_id
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
        """
        )
        categories, success_rates = [], []
        for row in cursor.fetchall():
            categories.append(row[0])
            success_rates.append(row[2] or 0)
        return categories, success_rates
    finally:
        conn.close()


def get_database_stats() -> dict:
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        stats: dict = {}
        cursor.execute("SELECT COUNT(*) FROM resume_data")
        stats["total_resumes"] = cursor.fetchone()[0]
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM resume_data
            WHERE DATE(created_at) = DATE('now')
        """
        )
        stats["today_submissions"] = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        size_bytes = page_count * page_size
        if size_bytes < 1024:
            stats["storage_size"] = f"{size_bytes} bytes"
        elif size_bytes < 1024 * 1024:
            stats["storage_size"] = f"{size_bytes/1024:.1f} KB"
        else:
            stats["storage_size"] = f"{size_bytes/(1024*1024):.1f} MB"
        return stats
    finally:
        conn.close()


def get_quick_stats() -> dict:
    conn = get_database_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM resume_data")
        total_resumes = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(ats_score) FROM resume_analysis")
        avg_ats = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM resume_analysis WHERE ats_score >= 70")
        high_performing = cursor.fetchone()[0]
        success_rate = (high_performing / total_resumes * 100) if total_resumes > 0 else 0
        return {
            "Total Resumes": f"{total_resumes:,}",
            "Avg ATS Score": f"{avg_ats:.1f}%",
            "High Performing": f"{high_performing:,}",
            "Success Rate": f"{success_rate:.1f}%",
        }
    finally:
        conn.close()
