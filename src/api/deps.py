"""Dependency injection for API routes."""

from src.database import get_db

__all__ = ["get_db"]
