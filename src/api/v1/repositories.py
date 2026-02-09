"""GET /repositories/{id} and GET /repositories/{id}/similar."""

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.deps import get_db
from src.models.repository import Repository
from src.models.content import GeneratedContent
from src.schemas.repository import ContentBlock, RepositoryDetail, SimilarRepo, TrendHistoryPoint

router = APIRouter()


@router.get("/repositories/{repo_id}", response_model=RepositoryDetail)
async def get_repository(
    repo_id: int,
    session: AsyncSession = Depends(get_db),
) -> RepositoryDetail:
    result = await session.execute(
        select(Repository)
        .where(Repository.id == repo_id)
        .options(
            selectinload(Repository.trend_snapshots),
            selectinload(Repository.generated_content),
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    snapshots = sorted(repo.trend_snapshots, key=lambda s: s.snapshot_at, reverse=True)[:48]
    trend_history = [
        TrendHistoryPoint(
            snapshot_at=s.snapshot_at,
            stars_count=s.stars_count,
            stars_delta_24h=s.stars_delta_24h,
            computed_trend_score=s.computed_trend_score,
        )
        for s in snapshots
    ]
    content: dict[str, ContentBlock] = {}
    for gc in repo.generated_content:
        content[gc.content_type] = ContentBlock(markdown=gc.content_markdown, generated_at=gc.generated_at)
    return RepositoryDetail(
        id=repo.id,
        full_name=repo.full_name,
        description=repo.description,
        html_url=repo.html_url,
        homepage_url=repo.homepage_url,
        primary_language=repo.primary_language,
        topics=list(repo.topics or []),
        license_spdx=repo.license_spdx,
        stars_count=repo.stars_count,
        forks_count=repo.forks_count,
        open_issues_count=repo.open_issues_count,
        pushed_at_gh=repo.pushed_at_gh,
        current_trend_score=repo.current_trend_score,
        quality_passed=repo.quality_passed,
        trend_history=trend_history,
        content=content,
    )


@router.get("/repositories/{repo_id}/similar", response_model=list[SimilarRepo])
async def get_similar_repositories(
    repo_id: int,
    session: AsyncSession = Depends(get_db),
    limit: int = Query(5, ge=1, le=20),
) -> list[SimilarRepo]:
    from src.models.embedding import RepoEmbedding

    repo_result = await session.execute(
        select(Repository).where(Repository.id == repo_id).options(selectinload(Repository.repo_embedding))
    )
    repo = repo_result.scalar_one_or_none()
    if not repo or not repo.repo_embedding:
        return []
    vec = repo.repo_embedding.embedding
    if hasattr(vec, "__iter__") and not isinstance(vec, str):
        vec = list(vec)
    else:
        return []
    dist_col = RepoEmbedding.embedding.cosine_distance(vec)
    similar_result = await session.execute(
        select(RepoEmbedding.repository_id, dist_col.label("dist"))
        .where(RepoEmbedding.repository_id != repo_id)
        .order_by(dist_col)
        .limit(limit)
    )
    rows = similar_result.all()
    if not rows:
        return []
    ids = [r[0] for r in rows]
    repos_result = await session.execute(select(Repository).where(Repository.id.in_(ids)))
    repos = {r.id: r for r in repos_result.scalars().all()}
    out = []
    for rid in ids:
        r = repos.get(rid)
        if r:
            out.append(SimilarRepo(id=r.id, full_name=r.full_name, description=r.description, stars_count=r.stars_count))
    return out
