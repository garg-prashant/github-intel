"""GET /stats — dashboard stats."""

from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_db
from src.models.repository import Repository
from src.models.content import GeneratedContent
from src.models.repository import TrendSnapshot
from src.schemas.stats import LanguageCount, StatsResponse

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
async def get_stats(session: AsyncSession = Depends(get_db)) -> StatsResponse:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    total = (await session.execute(select(func.count(Repository.id)))).scalar() or 0
    repos_today = (
        await session.execute(select(func.count(Repository.id)).where(Repository.first_seen_at >= today_start))
    ).scalar() or 0
    content_today = (
        await session.execute(select(func.count(GeneratedContent.id)).where(GeneratedContent.generated_at >= today_start))
    ).scalar() or 0
    top_lang = await session.execute(
        select(Repository.primary_language, func.count(Repository.id))
        .where(Repository.primary_language.isnot(None))
        .group_by(Repository.primary_language)
        .order_by(func.count(Repository.id).desc())
        .limit(10)
    )
    top_languages = [LanguageCount(language=row[0], count=row[1]) for row in top_lang.all()]
    last_snap = (await session.execute(select(func.max(TrendSnapshot.snapshot_at)))).scalar()
    return StatsResponse(
        total_tracked_repos=total,
        repos_added_today=repos_today,
        content_generated_today=content_today,
        top_languages=top_languages,
        last_ingestion_at=last_snap,
    )
