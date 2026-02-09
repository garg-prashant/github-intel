"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings
from src.models.base import Base


def get_engine(database_url: str | None = None):
    """Create async engine. Uses settings if url not provided."""
    url = database_url or Settings().database_url
    return create_async_engine(
        url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


def get_session_factory(engine=None):
    """Create async session factory."""
    if engine is None:
        engine = get_engine()
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


# Default engine and session factory (injected with settings at runtime)
engine = get_engine()
SessionLocal = get_session_factory(engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async session and closes it after use."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def session_scope():
    """Context manager for use outside FastAPI (e.g. scripts, Celery tasks).

    Creates a new engine and session in the current event loop so it is safe
    to use from forked Celery workers (where the global engine is bound to
    the parent's loop and would raise 'Future attached to a different loop').
    """
    _engine = get_engine()
    _session_factory = get_session_factory(_engine)
    try:
        async with _session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    finally:
        await _engine.dispose()
