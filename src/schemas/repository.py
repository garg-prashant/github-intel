"""Repository detail and related schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TrendHistoryPoint(BaseModel):
    snapshot_at: datetime
    stars_count: int
    stars_delta_24h: int | None
    computed_trend_score: float | None


class ContentBlock(BaseModel):
    markdown: str
    generated_at: datetime


class RepositoryDetail(BaseModel):
    id: int
    full_name: str
    description: str | None
    html_url: str
    homepage_url: str | None
    primary_language: str | None
    topics: list[str] = Field(default_factory=list)
    license_spdx: str | None
    stars_count: int
    forks_count: int
    open_issues_count: int
    pushed_at_gh: datetime
    current_trend_score: float | None
    quality_passed: bool
    trend_history: list[TrendHistoryPoint] = Field(default_factory=list)
    content: dict[str, ContentBlock] = Field(default_factory=dict)


class SimilarRepo(BaseModel):
    id: int
    full_name: str
    description: str | None
    stars_count: int
    similarity: float | None = None
