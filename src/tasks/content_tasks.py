"""Content generation tasks: generate LLM content for top repos."""

import asyncio
import logging

from src.celery_app import celery
from src.database import session_scope
from src.services.content_generation.service import generate_content_for_top_repos

logger = logging.getLogger(__name__)


@celery.task(bind=True, acks_late=True, max_retries=3)
def generate_content_for_top_repos_task(self) -> None:
    """Generate content for top N repos (cap per day and per cycle)."""
    try:
        async def _run() -> int:
            async with session_scope() as session:
                return await generate_content_for_top_repos(session)

        n = asyncio.run(_run())
        logger.info("generate_content_for_top_repos: created %s content rows", n)
    except Exception as exc:
        logger.exception("generate_content_for_top_repos failed: %s", exc)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
