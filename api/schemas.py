"""
Pydantic models for FastAPI (Phase 2 contract: analysis, resume build, feedback).
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class AnalysisRequest(BaseModel):
    """Job targeting context for ATS analysis (multipart form fields map here)."""

    job_category: str = Field(
        ...,
        description="Key from JOB_ROLES, e.g. 'Software Development and Engineering'",
    )
    job_role: str = Field(..., description="Role key, e.g. 'Backend Developer'")
    save_to_db: bool = Field(
        True,
        description="Persist resume + analysis to SQLite",
    )


class AIAnalysisRequest(AnalysisRequest):
    """Extended analysis context for Gemini / Claude."""

    custom_job_description: str = Field(
        "",
        description="Optional job description text; overrides built-in role_info when non-empty.",
    )
    model: str = Field(
        "Google Gemini",
        description='AI backend label: "Google Gemini" or "Anthropic Claude"',
    )


class ResumeData(BaseModel):
    """Payload for resume generation (matches Streamlit resume_data / ResumeBuilder)."""

    personal_info: dict[str, Any]
    summary: str = ""
    experience: list[Any] = Field(default_factory=list)
    education: list[Any] = Field(default_factory=list)
    projects: list[Any] = Field(default_factory=list)
    skills: dict[str, Any] = Field(default_factory=dict)
    template: str = "Modern"
    output_format: Literal["docx", "pdf"] = "docx"
    save_to_db: bool = True


class Feedback(BaseModel):
    """
    User feedback: required rating + comment (Phase 2).
    Extended fields match SQLite feedback table and Streamlit form.
    """

    rating: int = Field(..., ge=1, le=5)
    comment: str = ""
    usability_score: int | None = Field(None, ge=1, le=5)
    feature_satisfaction: int | None = Field(None, ge=1, le=5)
    missing_features: str = ""
    improvement_suggestions: str = ""
    user_experience: str = ""

    @model_validator(mode="after")
    def _defaults(self) -> Feedback:
        if self.usability_score is None:
            object.__setattr__(self, "usability_score", self.rating)
        if self.feature_satisfaction is None:
            object.__setattr__(self, "feature_satisfaction", self.rating)
        if self.comment.strip() and not str(self.user_experience).strip():
            object.__setattr__(self, "user_experience", self.comment.strip())
        return self


class AdminLoginRequest(BaseModel):
    email: str
    password: str


# Backward-compatible name used in OpenAPI / imports
ResumeBuildRequest = ResumeData

# Backward-compatible alias for feedback body
FeedbackSubmitRequest = Feedback
