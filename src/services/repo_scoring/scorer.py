"""Trend score: weighted formula with min-max normalization over cohort."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

# Weights per spec: stars_24h 0.4, forks_24h 0.2, commits_7d 0.15, issue_activity 0.15, recency 0.1
W_STARS_24H = 0.4
W_FORKS_24H = 0.2
W_COMMITS_7D = 0.15
W_ISSUE_ACTIVITY = 0.15
W_RECENCY = 0.1
RECENCY_DECAY_DAYS = 10


def _normalize(values: list[float], min_val: float | None = None, max_val: float | None = None) -> list[float]:
    """Normalize to 0-100 via min-max. If all same or empty, return 0s."""
    if not values:
        return []
    lo = min_val if min_val is not None else min(values)
    hi = max_val if max_val is not None else max(values)
    span = hi - lo
    if span <= 0:
        return [0.0] * len(values)
    return [max(0, min(100, (v - lo) / span * 100)) for v in values]


def recency_boost(pushed_at: datetime) -> float:
    """max(0, 10 - days_since_last_push)."""
    now = datetime.now(timezone.utc)
    if pushed_at.tzinfo is None:
        pushed_at = pushed_at.replace(tzinfo=timezone.utc)
    days = (now - pushed_at).total_seconds() / 86400
    return max(0.0, RECENCY_DECAY_DAYS - days)


def compute_trend_scores(
    repo_snapshots: list[tuple[int, int | None, int | None, int | None, int | None, datetime]],
) -> list[tuple[int, float]]:
    """
    repo_snapshots: list of (repo_id, stars_delta_24h, forks_delta_24h, commits_7d, issue_events_7d, pushed_at_gh).
    Returns list of (repo_id, trend_score) with scores normalized 0-100 for the cohort.
    """
    if not repo_snapshots:
        return []

    stars_24h = [(s[1] or 0) for s in repo_snapshots]
    forks_24h = [(s[2] or 0) for s in repo_snapshots]
    commits_7d = [(s[3] or 0) for s in repo_snapshots]
    issue_activity = [(s[4] or 0) for s in repo_snapshots]
    recency = [recency_boost(s[5]) for s in repo_snapshots]

    n_star = _normalize(stars_24h)
    n_fork = _normalize(forks_24h)
    n_commit = _normalize(commits_7d)
    n_issue = _normalize(issue_activity)
    n_rec = _normalize(recency)

    out: list[tuple[int, float]] = []
    for i, (repo_id, *_) in enumerate(repo_snapshots):
        score = (
            n_star[i] * W_STARS_24H
            + n_fork[i] * W_FORKS_24H
            + n_commit[i] * W_COMMITS_7D
            + n_issue[i] * W_ISSUE_ACTIVITY
            + n_rec[i] * W_RECENCY
        )
        out.append((repo_id, round(score, 4)))
    return out
