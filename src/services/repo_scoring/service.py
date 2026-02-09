"""Scoring service: compute trend scores and set quality_passed on repositories."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.repository import Repository, TrendSnapshot
from src.services.repo_scoring.quality_filters import passes_quality_filters
from src.services.repo_scoring.scorer import compute_trend_scores

logger = logging.getLogger(__name__)

SNAPSHOT_LOOKBACK_HOURS = 48
RECENT_DAYS = 30


def _stars_gained_in_window(snapshots: list[TrendSnapshot], days: int) -> int | None:
    """Stars gained in the last `days` days from snapshot time-series."""
    if not snapshots:
        return None
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    sorted_snaps = sorted(snapshots, key=lambda s: s.snapshot_at)
    in_window = [s for s in sorted_snaps if s.snapshot_at >= cutoff]
    if not in_window:
        return None
    oldest = in_window[0]
    latest = in_window[-1]
    return max(0, latest.stars_count - oldest.stars_count)


async def score_and_filter_all(session: AsyncSession) -> int:
    """
    Load repos with their latest snapshot data, compute trend scores,
    update current_trend_score, stars_gained_30d, and quality_passed.
    Returns number of repos updated.
    """
    # Load all repos with their snapshots for latest metrics
    repos = await session.execute(
        select(Repository).where(Repository.id.isnot(None)).options(selectinload(Repository.trend_snapshots))
    )
    repos_list = list(repos.scalars().unique().all())
    if not repos_list:
        return 0

    # Build cohort: (repo_id, stars_delta_24h, forks_delta_24h, commits_7d, issue_events_7d, pushed_at_gh)
    cohort: list[tuple[int, int | None, int | None, int | None, int | None, datetime]] = []
    for repo in repos_list:
        snapshots = sorted(repo.trend_snapshots, key=lambda s: s.snapshot_at, reverse=True)
        latest = snapshots[0] if snapshots else None
        if not latest:
            continue
        cohort.append((
            repo.id,
            latest.stars_delta_24h,
            latest.forks_delta_24h,
            latest.commits_7d,
            latest.issue_events_7d,
            repo.pushed_at_gh,
        ))

    if not cohort:
        return 0

    scores = compute_trend_scores(cohort)
    score_by_id = {r_id: s for r_id, s in scores}

    for repo in repos_list:
        if repo.id not in score_by_id:
            continue
        score = score_by_id[repo.id]
        snapshots = sorted(repo.trend_snapshots, key=lambda s: s.snapshot_at, reverse=True)
        if snapshots:
            snapshots[0].computed_trend_score = score
        repo.current_trend_score = score
        repo.stars_gained_30d = _stars_gained_in_window(repo.trend_snapshots, RECENT_DAYS)
        repo.quality_passed = passes_quality_filters(repo)
        await session.commit()
    return len(score_by_id)
