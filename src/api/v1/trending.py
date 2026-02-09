"""GET /trending — paginated trending repos with filters."""

from fastapi import APIRouter, Depends, Query

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.models.category import Category, RepositoryCategory
from src.models.content import GeneratedContent
from src.models.repository import Repository
from src.schemas.common import PaginatedResponse
from src.schemas.trending import CategoryRef, TrendingRepoItem

router = APIRouter()


@router.get("/trending", response_model=PaginatedResponse[TrendingRepoItem])
async def get_trending(
    session: AsyncSession = Depends(get_db),
    category: str | None = Query(None),
    sort_by: str = Query("score", pattern="^(score|recency)$"),
    language: str | None = Query(None),
    mode: str = Query("overall", pattern="^(overall|recent)$"),
    quality: str = Query("passed", pattern="^(passed|all|not_passed)$", description="passed=only passing, all=all repos, not_passed=only not passing"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> PaginatedResponse[TrendingRepoItem]:
    # Quality filter: passed (default), all, not_passed
    if quality == "passed":
        quality_filter = Repository.quality_passed == True
    elif quality == "not_passed":
        quality_filter = Repository.quality_passed == False
    else:
        quality_filter = None  # all: no filter

    base_opts = (
            selectinload(Repository.repository_categories).selectinload(RepositoryCategory.category),
            selectinload(Repository.generated_content),
            selectinload(Repository.trend_snapshots),
        )
    q = select(Repository).options(*base_opts)
    if quality_filter is not None:
        q = q.where(quality_filter)
    count_q = select(Repository.id)
    if quality_filter is not None:
        count_q = count_q.where(quality_filter)
    if category:
        q = q.join(RepositoryCategory).join(Category).where(Category.slug == category)
    if language:
        q = q.where(Repository.primary_language == language)
    if mode == "recent":
        q = q.order_by(Repository.stars_gained_30d.desc().nullslast())
    elif sort_by == "score":
        q = q.order_by(Repository.current_trend_score.desc().nullslast())
    else:
        q = q.order_by(Repository.pushed_at_gh.desc())
    if category:
        count_q = count_q.join(RepositoryCategory).join(Category).where(Category.slug == category)
    if language:
        count_q = count_q.where(Repository.primary_language == language)
    count_q = select(func.count()).select_from(count_q.distinct().subquery())
    total = (await session.execute(count_q)).scalar() or 0
    q = q.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(q)
    repos = list(result.scalars().unique().all())

    # Get latest snapshot for stars_delta_24h (we don't have it on repo; use first snapshot in reverse order or add column)
    items: list[TrendingRepoItem] = []
    for repo in repos:
        categories = [
            CategoryRef(slug=c.category.slug, name=c.category.name)
            for c in repo.repository_categories
        ]
        topics = list(repo.topics or [])
        snippet = None
        for gc in repo.generated_content:
            if gc.content_type == "what_and_why":
                snippet = (gc.content_markdown or "")[:200]
                break
        latest_snap = next(
            (s for s in sorted(repo.trend_snapshots, key=lambda x: x.snapshot_at, reverse=True)),
            None,
        )
        stars_delta_24h = latest_snap.stars_delta_24h if latest_snap else None
        items.append(
            TrendingRepoItem(
                id=repo.id,
                full_name=repo.full_name,
                description=repo.description,
                stars_count=repo.stars_count,
                stars_delta_24h=stars_delta_24h,
                stars_gained_30d=repo.stars_gained_30d,
                current_trend_score=repo.current_trend_score,
                categories=categories,
                topics=topics,
                snippet=snippet,
            )
        )
    return PaginatedResponse(items=items, page=page, page_size=page_size, total=total)
