"""Pydantic BaseSettings for application configuration."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://github_intel:github_intel_dev@localhost:5432/github_intel",
        description="Async PostgreSQL connection URL",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for Celery broker and result backend",
    )

    # GitHub
    github_token: str | None = Field(default=None, description="GitHub PAT with public_repo scope")
    github_request_delay_seconds: float = Field(
        default=1.0, ge=0, le=60,
        description="Delay in seconds between processing each repo (avoids rate limits and 503s)",
    )
    repo_metadata_cache_hours: float = Field(
        default=24.0, ge=0, le=720,
        description="Hours to treat persisted repo metadata as fresh; skip GitHub API for repos updated within this window (0 = always fetch)",
    )

    # LLM
    llm_provider: Literal["openai", "anthropic"] = Field(default="openai")
    openai_api_key: str | None = Field(default=None)
    openai_model: str = Field(default="gpt-4o-mini")
    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-sonnet-4-20250514")

    # Embeddings: "openai" (paid) or "local" (free, sentence-transformers)
    embedding_provider: Literal["openai", "local"] = Field(
        default="local",
        description="Use local open-source model (no API cost) or OpenAI embeddings",
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="OpenAI: text-embedding-3-small. Local: sentence-transformers model name (e.g. all-MiniLM-L6-v2)",
    )

    # Content generation caps
    max_repos_per_day: int = Field(default=20, ge=1, le=200)
    max_repos_per_cycle: int = Field(default=5, ge=1, le=50)

    # Ingestion caps (avoid GitHub rate limits and reduce API/LLM cost)
    max_repos_per_category: int = Field(
        default=10, ge=1, le=50,
        description="Max repos to ingest per topic (search) and to use for content per category",
    )
    max_trending_repos: int = Field(
        default=25, ge=1, le=100,
        description="Max repos to fetch from trending scrape (total across all views)",
    )

    # Categories: optional JSON array of {slug, name, description, keywords}; if not set use defaults from constants
    categories_json: str | None = Field(
        default=None,
        alias="CATEGORIES",
        description="Optional JSON array of category objects (slug, name, description, keywords). If not set, default categories are used.",
    )

    # API — store as string so env doesn't require JSON; expose as list via cors_origins computed field
    cors_origins_raw: str = Field(
        default="http://localhost:3000",
        alias="CORS_ORIGINS",
        description="Allowed CORS origins (comma-separated)",
    )

    # App
    version: str = Field(default="0.1.0")

    @computed_field
    @property
    def categories(self) -> list[dict[str, Any]]:
        """Parse CATEGORIES JSON from env, or return default categories from constants."""
        from src.constants import DEFAULT_CATEGORIES

        if not self.categories_json or not self.categories_json.strip():
            return DEFAULT_CATEGORIES
        try:
            data = json.loads(self.categories_json)
            if isinstance(data, list) and len(data) > 0:
                return data
        except (json.JSONDecodeError, TypeError):
            pass
        return DEFAULT_CATEGORIES

    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS_ORIGINS into a list."""
        return [x.strip() for x in self.cors_origins_raw.split(",") if x.strip()] or ["http://localhost:3000"]
