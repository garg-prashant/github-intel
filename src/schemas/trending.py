"""Trending list and repo card schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CategoryRef(BaseModel):
    slug: str
    name: str


class TrendingRepoItem(BaseModel):
    id: int
    full_name: str
    description: str | None
    stars_count: int
    stars_delta_24h: int | None
    stars_gained_30d: int | None = None
    current_trend_score: float | None
    categories: list[CategoryRef] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    snippet: str | None = None
