"""Repository and TrendSnapshot models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    BigInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.category import RepositoryCategory
    from src.models.content import GeneratedContent
    from src.models.embedding import RepoEmbedding


class Repository(Base):
    """Core entity: one row per GitHub repo."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_url: Mapped[str] = mapped_column(String(512), nullable=False)
    homepage_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    primary_language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    languages_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    topics: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    license_spdx: Mapped[str | None] = mapped_column(String(64), nullable=True)
    has_readme: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    readme_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    stars_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    forks_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    open_issues_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    watchers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    default_branch: Mapped[str] = mapped_column(String(64), default="main", nullable=False)
    created_at_gh: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    pushed_at_gh: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    is_fork: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_mirror: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_trend_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    stars_gained_30d: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    quality_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    trend_snapshots: Mapped[list["TrendSnapshot"]] = relationship(
        "TrendSnapshot", back_populates="repository", cascade="all, delete-orphan"
    )
    repository_categories: Mapped[list["RepositoryCategory"]] = relationship(
        "RepositoryCategory", back_populates="repository", cascade="all, delete-orphan"
    )
    generated_content: Mapped[list["GeneratedContent"]] = relationship(
        "GeneratedContent", back_populates="repository", cascade="all, delete-orphan"
    )
    repo_embedding: Mapped["RepoEmbedding | None"] = relationship(
        "RepoEmbedding", back_populates="repository", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index(
            "ix_repositories_quality_score",
            "quality_passed",
            "current_trend_score",
            postgresql_ops={"current_trend_score": "DESC"},
        ),
    )


class TrendSnapshot(Base):
    """Hourly time-series of repo metrics."""

    __tablename__ = "trend_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    stars_count: Mapped[int] = mapped_column(Integer, nullable=False)
    forks_count: Mapped[int] = mapped_column(Integer, nullable=False)
    open_issues_count: Mapped[int] = mapped_column(Integer, nullable=False)
    watchers_count: Mapped[int] = mapped_column(Integer, nullable=False)
    stars_delta_1h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stars_delta_24h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    forks_delta_24h: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commits_7d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issue_events_7d: Mapped[int | None] = mapped_column(Integer, nullable=True)
    computed_trend_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    repository: Mapped["Repository"] = relationship("Repository", back_populates="trend_snapshots")

    __table_args__ = (
        Index("ix_trend_snapshots_repo_snapshot", "repository_id", "snapshot_at"),
    )
