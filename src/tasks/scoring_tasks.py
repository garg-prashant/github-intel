"""Scoring tasks: compute trend scores and quality_passed."""

import asyncio
import logging

from src.celery_app import celery
from src.database import session_scope
from src.services.repo_scoring.service import score_and_filter_all

logger = logging.getLogger(__name__)


@celery.task(bind=True, acks_late=True, max_retries=2)
def score_and_filter_all_task(self) -> None:
    """Compute trend scores and apply quality filters for all repos."""
    try:
        async def _run() -> int:
            async with session_scope() as session:
                return await score_and_filter_all(session)

        n = asyncio.run(_run())
        logger.info("score_and_filter_all: updated %s repos", n)
    except Exception as exc:
        logger.exception("score_and_filter_all failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
