"""
FastAPI backend for Smart AI Resume Analyzer.
Run: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
Set DATA_DIR (e.g. /app/data) so SQLite uses a mounted volume: {DATA_DIR}/resume_data.db
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import Annotated, Any, Literal

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response

from api.auth import create_access_token
from api.dashboard_metrics import collect_dashboard_metrics
from api.deps import get_current_admin_email
from api.schemas import (
    AdminLoginRequest,
    AIAnalysisRequest,
    AnalysisRequest,
    Feedback,
    ResumeData,
)
from config.database import (
    init_database,
    log_admin_action,
    save_ai_analysis_data,
    save_analysis_data,
    save_resume_data,
    verify_admin,
)
from config.courses import COURSES_BY_CATEGORY
from config.job_roles import JOB_ROLES
from dashboard.export_data import (
    export_resumes_csv_bytes,
    export_resumes_excel_bytes,
    export_resumes_json_str,
)
from feedback.feedback import FeedbackManager
from jobs.job_search import get_filter_options
from utils.ai_resume_analyzer import AIResumeAnalyzer
from utils.resume_analyzer import ResumeAnalyzer
from utils.resume_builder import ResumeBuilder

from jobs.linkedin_scraper import LinkedInScraper

logger = logging.getLogger(__name__)

resume_analyzer = ResumeAnalyzer()
ai_resume_analyzer = AIResumeAnalyzer()
resume_builder = ResumeBuilder()
feedback_manager = FeedbackManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    yield


app = FastAPI(title="Smart AI Resume Analyzer API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _resolve_role_info(job_category: str, job_role: str) -> dict[str, Any]:
    categories = JOB_ROLES.get(job_category)
    if not categories:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown job_category: {job_category!r}. Use a key from JOB_ROLES.",
        )
    role_info = categories.get(job_role)
    if not role_info:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown job_role {job_role!r} for category {job_category!r}.",
        )
    return role_info


def _extract_text_from_upload(
    upload: UploadFile, raw: bytes, filename: str
) -> str:
    name = (filename or "").lower()
    ct = (upload.content_type or "").lower()

    if name.endswith(".pdf") or "pdf" in ct:
        buf = io.BytesIO(raw)
        try:
            return resume_analyzer.extract_text_from_pdf(buf)
        except Exception as first:
            logger.warning("Primary PDF extraction failed: %s", first)
            buf.seek(0)
            try:
                return ai_resume_analyzer.extract_text_from_pdf(buf)
            except Exception as second:
                logger.exception("All PDF extraction methods failed")
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not read PDF: {second}",
                ) from second

    if name.endswith(".docx") or "wordprocessingml" in ct or "officedocument" in ct:
        buf = io.BytesIO(raw)
        try:
            return resume_analyzer.extract_text_from_docx(buf)
        except Exception as first:
            logger.warning("Primary DOCX extraction failed: %s", first)
            buf.seek(0)
            try:
                return ai_resume_analyzer.extract_text_from_docx(buf)
            except Exception as second:
                logger.exception("All DOCX extraction methods failed")
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not read DOCX: {second}",
                ) from second

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail="Unsupported or binary file; upload a PDF or DOCX resume.",
        ) from e


def _extract_text_for_ai(upload: UploadFile, raw: bytes, filename: str) -> str:
    """
    Match Streamlit AI analyzer: PDF/DOCX text is taken from AIResumeAnalyzer first,
    with ResumeAnalyzer as fallback.
    """
    name = (filename or "").lower()
    ct = (upload.content_type or "").lower()

    if name.endswith(".pdf") or "pdf" in ct:
        buf = io.BytesIO(raw)
        try:
            return ai_resume_analyzer.extract_text_from_pdf(buf)
        except Exception as first:
            logger.warning("AI PDF extraction failed, trying ResumeAnalyzer: %s", first)
            buf.seek(0)
            try:
                return resume_analyzer.extract_text_from_pdf(buf)
            except Exception as second:
                logger.exception("All PDF extraction methods failed")
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not read PDF: {second}",
                ) from second

    if name.endswith(".docx") or "wordprocessingml" in ct or "officedocument" in ct:
        buf = io.BytesIO(raw)
        try:
            return ai_resume_analyzer.extract_text_from_docx(buf)
        except Exception as first:
            logger.warning("AI DOCX extraction failed, trying ResumeAnalyzer: %s", first)
            buf.seek(0)
            try:
                return resume_analyzer.extract_text_from_docx(buf)
            except Exception as second:
                logger.exception("All DOCX extraction methods failed")
                raise HTTPException(
                    status_code=400,
                    detail=f"Could not read DOCX: {second}",
                ) from second

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail="Unsupported or binary file; upload a PDF or DOCX resume.",
        ) from e


def _persist_standard_analysis(
    analysis: dict[str, Any],
    job_category: str,
    job_role: str,
) -> None:
    if analysis.get("error"):
        return
    resume_data = {
        "personal_info": {
            "full_name": analysis.get("name", ""),
            "email": analysis.get("email", ""),
            "phone": analysis.get("phone", ""),
            "linkedin": analysis.get("linkedin", ""),
            "github": analysis.get("github", ""),
            "portfolio": analysis.get("portfolio", ""),
        },
        "summary": analysis.get("summary", ""),
        "target_role": job_role,
        "target_category": job_category,
        "education": analysis.get("education", []),
        "experience": analysis.get("experience", []),
        "projects": analysis.get("projects", []),
        "skills": analysis.get("skills", []),
        "template": "",
    }
    resume_id = save_resume_data(resume_data)
    if not resume_id:
        logger.warning("save_resume_data returned no resume_id")
        return
    kw = analysis.get("keyword_match") or {}
    analysis_data = {
        "ats_score": analysis["ats_score"],
        "keyword_match_score": kw.get("score", 0),
        "format_score": analysis["format_score"],
        "section_score": analysis["section_score"],
        "missing_skills": ",".join(kw.get("missing_skills", []) or []),
        "recommendations": ",".join(analysis.get("suggestions", []) or []),
    }
    save_analysis_data(resume_id, analysis_data)


def _form_to_analysis_request(
    job_category: str = Form(
        ...,
        description="Job category key, e.g. 'Software Development and Engineering'",
    ),
    job_role: str = Form(..., description="Role key, e.g. 'Backend Developer'"),
    save_to_db: bool = Form(
        True,
        description="Persist resume + analysis to SQLite (same as Streamlit)",
    ),
) -> AnalysisRequest:
    return AnalysisRequest(
        job_category=job_category,
        job_role=job_role,
        save_to_db=save_to_db,
    )


def _form_to_ai_analysis_request(
    job_category: str = Form(
        ...,
        description="Job category key from JOB_ROLES",
    ),
    job_role: str = Form(..., description="Role key from JOB_ROLES"),
    custom_job_description: str = Form(
        "",
        description="Optional full job description; when set, used as Gemini job context instead of role_info text",
    ),
    model: str = Form(
        "Google Gemini",
        description='AI backend: "Google Gemini" or "Anthropic Claude"',
    ),
    save_to_db: bool = Form(
        True,
        description="Persist a row to ai_analysis (same fields as Streamlit)",
    ),
) -> AIAnalysisRequest:
    return AIAnalysisRequest(
        job_category=job_category,
        job_role=job_role,
        save_to_db=save_to_db,
        custom_job_description=custom_job_description,
        model=model,
    )


def _unlink_later(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


def _docx_bytes_to_pdf(docx_bytes: bytes) -> bytes:
    """Convert DOCX bytes to PDF using docx2pdf (requires Microsoft Word on Windows)."""
    import os
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="resume_pdf_")
    try:
        docx_path = os.path.join(tmp, "resume.docx")
        pdf_path = os.path.join(tmp, "resume.pdf")
        with open(docx_path, "wb") as f:
            f.write(docx_bytes)
        try:
            from docx2pdf import convert
        except ImportError as e:
            raise HTTPException(
                status_code=501,
                detail="PDF export requires the docx2pdf package: pip install docx2pdf",
            ) from e
        convert(docx_path, pdf_path)
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError("PDF file was not produced")
        with open(pdf_path, "rb") as f:
            return f.read()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _attachment_filename(base: str, suffix: str) -> str:
    safe = "".join(c for c in base if c.isalnum() or c in (" ", "_", "-")).strip()
    safe = safe.replace(" ", "_")[:80] or "resume"
    return f'{safe}{suffix}'


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/config/job_roles")
def config_job_roles() -> dict[str, Any]:
    """Public read-only job role taxonomy for analyzer forms (same data as ``JOB_ROLES``)."""
    return JOB_ROLES


@app.get("/config/courses")
def config_courses() -> dict[str, Any]:
    """Public course recommendations by category / role."""
    return COURSES_BY_CATEGORY


@app.get("/config/job_filters")
def config_job_filters() -> dict[str, Any]:
    """Filter metadata for job search UIs (experience, salary, job type)."""
    return get_filter_options()


@app.post("/analyze/basic")
def analyze_basic(
    _admin_email: Annotated[str, Depends(get_current_admin_email)],
    req: Annotated[AnalysisRequest, Depends(_form_to_analysis_request)],
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
) -> dict[str, Any]:
    """
    Standard ATS-style analysis using ResumeAnalyzer.analyze_resume.
    Response JSON matches the analyzer dict keys (same as Streamlit).

    Form fields map to ``AnalysisRequest`` (``job_category``, ``job_role``, ``save_to_db``).

    **Requires** ``Authorization: Bearer`` (admin login).
    """
    role_info = _resolve_role_info(req.job_category, req.job_role)
    raw = file.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file upload")

    text = _extract_text_from_upload(file, raw, file.filename or "")

    if not text or not str(text).strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract any text from the uploaded file.",
        )

    analysis = resume_analyzer.analyze_resume({"raw_text": text}, role_info)

    if req.save_to_db:
        try:
            _persist_standard_analysis(analysis, req.job_category, req.job_role)
        except Exception as e:
            logger.exception("Database save failed after analysis: %s", e)

    return analysis


@app.post("/analyze/ai")
def analyze_ai(
    _admin_email: Annotated[str, Depends(get_current_admin_email)],
    req: Annotated[AIAnalysisRequest, Depends(_form_to_ai_analysis_request)],
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or plain text)"),
) -> dict[str, Any]:
    """
    Gemini (or Claude) analysis via AIResumeAnalyzer.analyze_resume.

    Form fields map to ``AIAnalysisRequest``.

    Success / error responses use the same keys as the Streamlit AI flow:
    ``score``, ``ats_score``, ``strengths``, ``weaknesses``, ``suggestions``,
    ``full_response``, ``model_used``, or ``error`` plus zeroed fields when the model fails.

    **Requires** ``Authorization: Bearer`` (admin login).
    """
    role_info = _resolve_role_info(req.job_category, req.job_role)
    raw = file.file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file upload")

    resume_text = _extract_text_for_ai(file, raw, file.filename or "")

    if not resume_text or not str(resume_text).strip():
        raise HTTPException(
            status_code=400,
            detail="Could not extract any text from the uploaded file.",
        )

    custom_jd = req.custom_job_description.strip() or None
    result = ai_resume_analyzer.analyze_resume(
        resume_text,
        job_role=req.job_role,
        role_info=role_info,
        model=req.model,
        custom_job_description=custom_jd,
    )

    if req.save_to_db and result.get("error") is None:
        try:
            save_ai_analysis_data(
                None,
                {
                    "model_used": result.get("model_used", req.model),
                    "resume_score": int(result.get("score") or 0),
                    "job_role": req.job_role,
                },
            )
        except Exception as e:
            logger.exception("save_ai_analysis_data failed: %s", e)

    return result


@app.post("/builder/generate")
def builder_generate(
    _admin_email: Annotated[str, Depends(get_current_admin_email)],
    background_tasks: BackgroundTasks,
    body: ResumeData,
) -> FileResponse:
    """
    Build a resume with ``ResumeBuilder.generate_resume`` and return a downloadable file.

    JSON body matches ``ResumeData`` (personal_info, sections, ``output_format``, etc.).

    - ``output_format=docx`` — same as Streamlit download (Word document).
    - ``output_format=pdf`` — converts DOCX via ``docx2pdf`` (typically needs Microsoft Word on Windows).

    Response uses ``FileResponse``. React clients should use ``responseType: 'blob'``.

    **Requires** ``Authorization: Bearer`` (admin login).
    """
    pi = body.personal_info
    if not str(pi.get("full_name", "")).strip():
        raise HTTPException(
            status_code=400,
            detail="personal_info.full_name is required (matches Streamlit validation).",
        )
    if not str(pi.get("email", "")).strip():
        raise HTTPException(
            status_code=400,
            detail="personal_info.email is required (matches Streamlit validation).",
        )

    data: dict[str, Any] = {
        "personal_info": dict(pi),
        "summary": body.summary,
        "experience": body.experience,
        "education": body.education,
        "projects": body.projects,
        "skills": body.skills,
        "template": body.template,
    }

    try:
        buffer = resume_builder.generate_resume(data)
        docx_bytes = buffer.getvalue()
    except Exception as e:
        logger.exception("generate_resume failed")
        raise HTTPException(status_code=500, detail=str(e)) from e

    if body.save_to_db:
        try:
            save_resume_data(data)
        except Exception as e:
            logger.exception("save_resume_data failed: %s", e)

    fname = _attachment_filename(
        str(pi.get("full_name", "resume")),
        "_resume.pdf" if body.output_format == "pdf" else "_resume.docx",
    )

    if body.output_format == "pdf":
        try:
            out_bytes = _docx_bytes_to_pdf(docx_bytes)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("DOCX to PDF conversion failed")
            raise HTTPException(
                status_code=503,
                detail=(
                    "Could not produce PDF. On Windows, docx2pdf requires Microsoft Word. "
                    f"Try output_format='docx' instead. Detail: {e!s}"
                ),
            ) from e
        suffix = ".pdf"
        media = "application/pdf"
    else:
        out_bytes = docx_bytes
        suffix = ".docx"
        media = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, out_bytes)
    finally:
        os.close(fd)
    background_tasks.add_task(_unlink_later, path)
    return FileResponse(
        path,
        filename=fname,
        media_type=media,
    )


@app.get("/dashboard/metrics")
def dashboard_metrics(
    _admin_email: Annotated[str, Depends(get_current_admin_email)],
) -> dict[str, Any]:
    """
    Statistical metrics from SQLite — same sources as ``DashboardManager`` / Streamlit dashboard
    (resume counts, ATS trends, skill distribution, AI analysis stats, etc.).

    **Requires** ``Authorization: Bearer &lt;token&gt;`` from ``POST /admin/login``.
    """
    return collect_dashboard_metrics()


@app.get("/admin/me")
def admin_me(
    admin_email: Annotated[str, Depends(get_current_admin_email)],
) -> dict[str, str]:
    """Return the admin identity embedded in a valid JWT (for React session checks)."""
    return {"email": admin_email}


@app.get("/jobs/search")
def jobs_search(
    _admin_email: Annotated[str, Depends(get_current_admin_email)],
    keywords: str = Query(
        ...,
        description="Comma-separated job titles, e.g. 'Data Scientist, Software Engineer'",
    ),
    location: str = Query(
        "India",
        description="Location (e.g. Bangalore, Remote, India)",
    ),
    job_count: int = Query(
        3,
        ge=1,
        le=10,
        description="How many listings to fetch (max 10; matches Streamlit)",
    ),
) -> dict[str, Any]:
    """
    Selenium LinkedIn job search. Requires Chrome and a working webdriver (see ``jobs/webdriver_utils``).

    Returns ``jobs`` (list of row dicts with columns like ``Company Name``, ``Job Title``, …) and
    ``count``, or an ``error`` message when scraping fails.

    **Requires** ``Authorization: Bearer`` (admin login).
    """
    titles = [t.strip() for t in keywords.split(",") if t.strip()]
    if not titles:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one non-empty keyword (comma-separated).",
        )
    loc = location.strip()
    if not loc:
        raise HTTPException(status_code=400, detail="location cannot be empty.")
    return LinkedInScraper.search_jobs_headless(titles, loc, job_count)


@app.post("/feedback")
def submit_feedback(body: Feedback) -> dict[str, str]:
    """
    Persist user feedback (``Feedback``: rating + comment; extended fields optional).

    Public endpoint (consider placing behind a reverse proxy / rate limit in production).
    """
    feedback_manager.save_feedback(body.model_dump())
    return {"status": "ok"}


@app.get("/admin/feedback/stats")
def admin_feedback_stats(
    _admin_email: Annotated[str, Depends(get_current_admin_email)],
) -> dict[str, Any]:
    """Aggregated feedback statistics from ``feedback.db``."""
    return feedback_manager.get_feedback_stats()


@app.get("/admin/export/resumes")
def admin_export_resumes(
    _admin_email: Annotated[str, Depends(get_current_admin_email)],
    export_format: Literal["excel", "csv", "json"] = Query(
        "excel",
        description="Download format",
    ),
) -> Response:
    """Export joined resume + analysis tables (admin only)."""
    if export_format == "excel":
        data = export_resumes_excel_bytes()
        if not data:
            raise HTTPException(status_code=500, detail="Export failed")
        return Response(
            content=data,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": 'attachment; filename="resume_export.xlsx"'
            },
        )
    if export_format == "csv":
        data = export_resumes_csv_bytes()
        if not data:
            raise HTTPException(status_code=500, detail="Export failed")
        return Response(
            content=data,
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="resume_export.csv"'},
        )
    raw = export_resumes_json_str()
    if not raw:
        raise HTTPException(status_code=500, detail="Export failed")
    return Response(
        content=raw.encode("utf-8"),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="resume_export.json"'},
    )


@app.post("/admin/login")
def admin_login(body: AdminLoginRequest) -> dict[str, Any]:
    """
    Validates credentials via ``verify_admin`` and returns a JWT (HS256, configurable ``JWT_SECRET``).

    Send the token as ``Authorization: Bearer &lt;access_token&gt;`` on all routes except
    ``/health``, ``/admin/login``, and public ``/config/*`` endpoints.
    """
    if not verify_admin(body.email, body.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    try:
        log_admin_action(body.email, "login_api")
    except Exception:
        logger.exception("log_admin_action failed")
    token = create_access_token(body.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "email": body.email,
    }
