"""Combined classifier: 0.4 * embedding + 0.35 * keyword + 0.25 * language; assign if > 0.3."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.category import Category, RepositoryCategory
from src.models.repository import Repository
from src.services.classification.embedding_classifier import (
    embedding_confidences_for_repo,
    ensure_repo_embedding,
)
from src.services.classification.keyword_heuristics import keyword_confidence
from src.services.classification.language_analyzer import language_confidence

logger = logging.getLogger(__name__)

W_EMBEDDING = 0.4
W_KEYWORD = 0.35
W_LANGUAGE = 0.25
MIN_COMBINED = 0.3
METHOD = "combined"


async def classify_new_repos(session: AsyncSession, limit: int = 500) -> int:
    """
    Find repos without repository_categories (or with fewer than 2), compute combined
    confidence per category, insert repository_categories where combined >= MIN_COMBINED.
    Returns number of repo-category pairs assigned.
    """
    categories_result = await session.execute(select(Category))
    categories = list(categories_result.scalars().all())
    if not categories:
        return 0

    # Repos that have no categories yet (or we could process all and upsert)
    repos_result = await session.execute(
        select(Repository)
        .options(selectinload(Repository.repository_categories), selectinload(Repository.repo_embedding))
        .limit(limit * 2)
    )
    repos = list(repos_result.scalars().unique().all())
    # Prefer unclassified
    unclassified = [r for r in repos if not r.repository_categories]
    to_process = unclassified[:limit] if unclassified else repos[:limit]
    if not to_process:
        return 0

    assigned = 0
    for repo in to_process:
        try:
            repo_emb = await ensure_repo_embedding(session, repo)
            kw = {c.id: keyword_confidence(repo, c) for c in categories}
            lang = {c.id: language_confidence(repo, c) for c in categories}
            emb_conf = await embedding_confidences_for_repo(session, repo, categories, repo_emb)
            for cat in categories:
                cid = cat.id
                combined = (
                    W_EMBEDDING * emb_conf.get(cid, 0)
                    + W_KEYWORD * kw.get(cid, 0)
                    + W_LANGUAGE * lang.get(cid, 0)
                )
                if combined < MIN_COMBINED:
                    continue
                ins = pg_insert(RepositoryCategory).values(
                    repository_id=repo.id,
                    category_id=cid,
                    confidence=round(combined, 4),
                    classification_method=METHOD,
                )
                stmt = ins.on_conflict_do_update(
                    index_elements=["repository_id", "category_id"],
                    set_={
                        RepositoryCategory.confidence: ins.excluded.confidence,
                        RepositoryCategory.classification_method: ins.excluded.classification_method,
                        RepositoryCategory.assigned_at: datetime.now(timezone.utc),
                    },
                )
                await session.execute(stmt)
                assigned += 1
        except Exception as e:
            logger.warning("Classification failed for repo %s: %s", repo.full_name, e)
    await session.commit()
    return assigned
