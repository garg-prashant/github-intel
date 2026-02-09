"""SQLAlchemy DeclarativeBase and shared mixins."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)
