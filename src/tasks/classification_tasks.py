"""Classification tasks: assign categories to repos (keyword + embedding + language)."""

import asyncio
import logging

from src.celery_app import celery
from src.database import session_scope
from src.services.classification.service import classify_new_repos

logger = logging.getLogger(__name__)


@celery.task(bind=True, acks_late=True, max_retries=2)
def classify_new_repos_task(self) -> None:
    """Classify unclassified repos with combined keyword/embedding/language signals."""
    try:
        async def _run() -> int:
            async with session_scope() as session:
                return await classify_new_repos(session, limit=500)

        n = asyncio.run(_run())
        logger.info("classify_new_repos: assigned %s repo-category pairs", n)
    except Exception as exc:
        logger.exception("classify_new_repos failed: %s", exc)
        raise self.retry(exc=exc, countdown=60)
