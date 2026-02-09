"""Stats endpoint schema."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LanguageCount(BaseModel):
    language: str
    count: int


class StatsResponse(BaseModel):
    total_tracked_repos: int  # all repos in DB (ingested)
    repos_passing_quality: int  # repos shown on dashboard (quality_passed=True)
    repos_added_today: int
    content_generated_today: int
    top_languages: list[LanguageCount] = Field(default_factory=list)
    last_ingestion_at: datetime | None = None
