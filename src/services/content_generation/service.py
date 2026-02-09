"""Content generation service: pick top repos, generate all 5 content types, respect daily/cycle caps."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config import Settings
from src.llm.factory import create_llm
from src.models.category import Category, RepositoryCategory
from src.models.content import CONTENT_TYPES, GeneratedContent
from src.models.repository import Repository
from src.services.content_generation.generator import generate_one

logger = logging.getLogger(__name__)


async def generate_content_for_top_repos(session: AsyncSession) -> int:
    """
    Select up to max_repos_per_category repos per category (quality_passed, in that category,
    fewest content rows first, then by trend score). Generate content subject to daily cap.
    """
    settings = Settings()
    max_per_cat = settings.max_repos_per_category
    max_per_day = settings.max_repos_per_day

    # Count how many content rows we've created today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    day_count_result = await session.execute(
        select(func.count(GeneratedContent.id)).where(GeneratedContent.generated_at >= today_start)
    )
    day_count = day_count_result.scalar() or 0
    remaining_today = max(0, max_per_day - day_count)
    if remaining_today <= 0:
        logger.info("Daily content cap reached (%s)", max_per_day)
        return 0

    subq = (
        select(Repository.id.label("rid"), func.count(GeneratedContent.id).label("cnt"))
        .select_from(Repository)
        .outerjoin(GeneratedContent, Repository.id == GeneratedContent.repository_id)
        .where(Repository.quality_passed == True)
        .group_by(Repository.id)
    )
    sq = subq.subquery()

    # Top N repo ids per category (repos with < 5 content types, joined via RepositoryCategory)
    category_ids_result = await session.execute(select(Category.id))
    category_ids = [r[0] for r in category_ids_result.all()]
    top_repo_ids: set[int] = set()
    for cat_id in category_ids:
        stmt = (
            select(Repository.id)
            .join(RepositoryCategory, Repository.id == RepositoryCategory.repository_id)
            .join(sq, Repository.id == sq.c.rid)
            .where(RepositoryCategory.category_id == cat_id, sq.c.cnt < len(CONTENT_TYPES))
            .order_by(sq.c.cnt.asc(), Repository.current_trend_score.desc().nullslast())
            .limit(max_per_cat)
        )
        result = await session.execute(stmt)
        for row in result.all():
            top_repo_ids.add(row[0])

    if not top_repo_ids:
        return 0

    repos_result = await session.execute(
        select(Repository)
        .where(Repository.id.in_(top_repo_ids))
        .order_by(Repository.current_trend_score.desc().nullslast())
        .options(selectinload(Repository.generated_content))
    )
    repos = list(repos_result.scalars().unique().all())

    llm = create_llm(settings)
    created = 0
    for repo in repos:
        if created >= remaining_today:
            break
        existing_types = {gc.content_type for gc in repo.generated_content}
        for content_type in CONTENT_TYPES:
            if content_type in existing_types:
                continue
            if created >= remaining_today:
                break
            row = await generate_one(session, repo, content_type, llm)
            if row:
                created += 1
                existing_types.add(content_type)
        await session.commit()
    return created
