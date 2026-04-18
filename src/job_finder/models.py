from __future__ import annotations

from pydantic import BaseModel, Field


class JobRecord(BaseModel):
    source: str
    company: str | None = None
    title: str
    url: str
    location_raw: str | None = None
    country: str | None = None
    remote_type: str | None = None
    description_html: str | None = None
    description_text: str = ""
    employment_type: str | None = None
    salary_raw: str | None = None
    posted_at: str | None = None

    relevance_score: float | None = None
    relevance_label: str | None = None
    llm_reason: str | None = None
    rule_reason: str | None = None
    classification_confidence: float | None = None
    is_relevant: bool | None = None
    matched_signals: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)

    job_hash: str


class ClassificationResult(BaseModel):
    is_relevant: bool
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    score: float = Field(ge=0.0, le=100.0)
    why_relevant: str = ""
    why_not_relevant: str = ""
    matched_signals: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
