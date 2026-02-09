"""Health check endpoint."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.config import Settings

router = APIRouter()


@router.get("/health", response_model=dict[str, Any])
async def health(session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Return status, DB and Redis connectivity, and version."""
    settings = Settings()
    db_status = "disconnected"
    try:
        await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        pass

    redis_status = "disconnected"
    try:
        import redis.asyncio as redis
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        redis_status = "connected"
    except Exception:
        pass

    return {
        "status": "healthy",
        "db": db_status,
        "redis": redis_status,
        "version": settings.version,
    }
