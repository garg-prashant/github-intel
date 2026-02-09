"""Quality filters — all must pass for quality_passed=True."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from src.models.repository import Repository

ACTIVE_DAYS = 14
MIN_DESCRIPTION_LEN = 20
MIN_STARS = 5


def passes_quality_filters(repo: Repository) -> bool:
    """Return True if repo passes all quality filters."""
    if not repo.has_readme:
        return False
    if repo.license_spdx is None or repo.license_spdx.strip() == "":
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=ACTIVE_DAYS)
    if repo.pushed_at_gh < cutoff:
        return False
    if repo.is_fork or repo.is_archived or repo.is_mirror:
        return False
    desc = (repo.description or "").strip()
    if len(desc) < MIN_DESCRIPTION_LEN:
        return False
    if (repo.stars_count or 0) < MIN_STARS:
        return False
    return True
