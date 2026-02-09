"""Ingestion tasks: trending scrape, search API, cleanup snapshots."""

import asyncio
import logging

from src.celery_app import celery
from src.database import session_scope
from src.services.trend_ingestion.service import TrendIngestionService

logger = logging.getLogger(__name__)


async def _run_trending_ingestion() -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.ingest_from_trending_pages()


async def _run_search_ingestion() -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.ingest_from_search_api()


async def _run_cleanup(days: int = 30) -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.cleanup_old_snapshots(older_than_days=days)


@celery.task(bind=True, acks_late=True, max_retries=3)
def ingest_trending_repos(self) -> None:
    """Scrape github.com/trending and upsert repos + snapshots."""
    try:
        n = asyncio.run(_run_trending_ingestion())
        logger.info("ingest_trending_repos: processed %s repos", n)
    except Exception as exc:
        logger.exception("ingest_trending_repos failed: %s", exc)
        raise self.retry(exc=exc, countdown=120 * (2 ** self.request.retries))


@celery.task(bind=True, acks_late=True, max_retries=3)
def ingest_search_api_repos(self) -> None:
    """Run GitHub Search API queries per category and upsert repos + snapshots."""
    try:
        n = asyncio.run(_run_search_ingestion())
        logger.info("ingest_search_api_repos: processed %s repos", n)
    except Exception as exc:
        logger.exception("ingest_search_api_repos failed: %s", exc)
        raise self.retry(exc=exc, countdown=180 * (2 ** self.request.retries))


@celery.task(bind=True, acks_late=True, max_retries=1)
def cleanup_old_snapshots(self) -> None:
    """Delete trend_snapshots older than 30 days."""
    try:
        n = asyncio.run(_run_cleanup(30))
        logger.info("cleanup_old_snapshots: deleted %s rows", n)
    except Exception as exc:
        logger.exception("cleanup_old_snapshots failed: %s", exc)
        raise self.retry(exc=exc, countdown=300)
