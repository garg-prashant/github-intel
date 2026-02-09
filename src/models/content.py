"""GeneratedContent model — LLM output per content type per repo."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.repository import Repository

CONTENT_TYPES = (
    "what_and_why",
    "quick_start",
    "mental_model",
    "practical_recipe",
    "learning_path",
)


class GeneratedContent(Base):
    """One row per content type per repo (what_and_why, quick_start, etc.)."""

    __tablename__ = "generated_content"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repository_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False
    )
    content_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    llm_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    llm_model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(16), default="v1", nullable=False)
    token_usage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    repository: Mapped["Repository"] = relationship("Repository", back_populates="generated_content")

    __table_args__ = (
        UniqueConstraint(
            "repository_id", "content_type", "prompt_version", name="uq_generated_content_repo_type_version"
        ),
    )
