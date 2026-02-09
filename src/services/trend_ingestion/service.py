"""Orchestration: topic-based search, fetch metadata, upsert repos, create snapshots."""

from __future__ import annotations

import asyncio
import base64
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.models.repository import Repository, TrendSnapshot
from src.services.trend_ingestion.github_client import GitHubClient
from src.services.trend_ingestion.scrapers import scrape_trending_full_names

logger = logging.getLogger(__name__)

README_MAX_CHARS = 15_000

# Topic-based discovery (GitHub search: https://github.com/search?q=agent&type=repositories)
TOPIC_SEARCH_TERMS: list[str] = ["AI", "agent", "MCP", "crypto"]
ALLOWED_LANGUAGES: frozenset[str] = frozenset({"Go", "Python", "TypeScript", "JavaScript"})
MIN_STARS_TOPIC = 10


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _repo_from_api(data: dict[str, Any]) -> dict[str, Any]:
    """Build Repository row dict from GitHub API repo response."""
    owner = (data.get("owner") or {}).get("login") or ""
    name = data.get("name") or ""
    full_name = data.get("full_name") or f"{owner}/{name}"
    pushed_at = _parse_iso(data.get("pushed_at")) or datetime.now(timezone.utc)
    created_at_gh = _parse_iso(data.get("created_at")) or pushed_at
    license_obj = data.get("license")
    license_spdx = license_obj.get("spdx_id") if isinstance(license_obj, dict) else None
    if license_spdx == "NOASSERTION":
        license_spdx = None
    return {
        "github_id": data.get("id"),
        "full_name": full_name,
        "owner": owner,
        "name": name,
        "description": (data.get("description") or "")[: 2**31 - 1] if data.get("description") else None,
        "html_url": data.get("html_url") or "",
        "homepage_url": (data.get("homepage") or "")[:512] if data.get("homepage") else None,
        "primary_language": (data.get("language") or "")[:64] if data.get("language") else None,
        "topics": data.get("topics") if isinstance(data.get("topics"), list) else None,
        "license_spdx": license_spdx,
        "has_readme": False,
        "readme_content": None,
        "stars_count": data.get("stargazers_count") or 0,
        "forks_count": data.get("forks_count") or 0,
        "open_issues_count": data.get("open_issues_count") or 0,
        "watchers_count": data.get("watchers_count") or 0,
        "default_branch": (data.get("default_branch") or "main")[:64],
        "created_at_gh": created_at_gh,
        "pushed_at_gh": pushed_at,
        "is_fork": bool(data.get("fork")),
        "is_archived": bool(data.get("archived")),
        "is_mirror": bool(data.get("mirror_url")),
    }


def _decode_readme(content_b64: str | None, encoding: str | None) -> str | None:
    if not content_b64:
        return None
    try:
        raw = base64.b64decode(content_b64)
        if encoding == "base64":
            return raw.decode("utf-8", errors="replace")
        return raw.decode(encoding or "utf-8", errors="replace")
    except Exception:
        return None


def _repo_cache_fresh(repo: Repository, cache_hours: float) -> bool:
    """True if repo was updated within cache window."""
    if cache_hours <= 0:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cache_hours)
    return repo.updated_at >= cutoff


class TrendIngestionService:
    """Run trending scrape, GitHub API fetch, and DB upsert + snapshots."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_cached_repo(self, full_name: str) -> Repository | None:
        """Return repo if it exists and metadata is still fresh (within cache window)."""
        result = await self.session.execute(
            select(Repository).where(Repository.full_name == full_name)
        )
        repo = result.scalar_one_or_none()
        if repo is None:
            return None
        if not _repo_cache_fresh(repo, Settings().repo_metadata_cache_hours):
            return None
        return repo

    async def _add_snapshot_from_cached_repo(self, repo: Repository) -> None:
        """Create a new TrendSnapshot from cached repo row (no GitHub API calls)."""
        prev = await self.session.execute(
            select(TrendSnapshot)
            .where(TrendSnapshot.repository_id == repo.id)
            .order_by(TrendSnapshot.snapshot_at.desc())
            .limit(2)
        )
        prev_snapshots = list(prev.scalars().all())
        stars_delta_1h: int | None = None
        stars_delta_24h: int | None = None
        forks_delta_24h: int | None = None
        if len(prev_snapshots) >= 1:
            stars_delta_1h = repo.stars_count - prev_snapshots[0].stars_count
        if len(prev_snapshots) >= 2:
            stars_delta_24h = repo.stars_count - prev_snapshots[1].stars_count
            forks_delta_24h = repo.forks_count - prev_snapshots[1].forks_count
        snapshot = TrendSnapshot(
            repository_id=repo.id,
            stars_count=repo.stars_count,
            forks_count=repo.forks_count,
            open_issues_count=repo.open_issues_count,
            watchers_count=repo.watchers_count,
            stars_delta_1h=stars_delta_1h,
            stars_delta_24h=stars_delta_24h,
            forks_delta_24h=forks_delta_24h,
            commits_7d=None,
        )
        self.session.add(snapshot)

    async def ingest_from_trending_pages(self) -> int:
        """Scrape trending, fetch each repo (capped), upsert + snapshot. Returns count of repos processed."""
        full_names = await scrape_trending_full_names()
        if not full_names:
            logger.warning("No repos from trending scrape")
            return 0
        max_trending = Settings().max_trending_repos
        if len(full_names) > max_trending:
            full_names = full_names[:max_trending]
            logger.info("Capping trending repos to %s", max_trending)
        return await self._fetch_and_upsert_repos(full_names)

    async def ingest_from_topic_search(self) -> int:
        """Discover repos via topic search (AI, agent, MCP, crypto), filter by language (Go, Python, TypeScript, JavaScript), then upsert."""
        settings = Settings()
        max_per_topic = settings.max_repos_per_category
        total_cap = settings.max_trending_repos
        seen: dict[str, int] = {}  # full_name -> stars_count for dedupe and sort
        async with GitHubClient() as client:
            for topic in TOPIC_SEARCH_TERMS:
                query = f"topic:{topic} stars:>{MIN_STARS_TOPIC}"
                try:
                    data = await client.search_repositories(query, page=1, per_page=max_per_topic)
                    items = data.get("items") or []
                    for item in items:
                        lang = item.get("language")
                        if lang not in ALLOWED_LANGUAGES:
                            continue
                        fn = item.get("full_name")
                        if not fn:
                            continue
                        stars = item.get("stargazers_count") or 0
                        if fn not in seen or seen[fn] < stars:
                            seen[fn] = stars
                except Exception as e:
                    logger.warning("Topic search failed %s: %s", query, e)
        if not seen:
            logger.warning("No repos from topic search (topics=%s, languages=%s)", TOPIC_SEARCH_TERMS, list(ALLOWED_LANGUAGES))
            return 0
        # Sort by stars desc, take up to total_cap
        full_names = [fn for fn, _ in sorted(seen.items(), key=lambda x: -x[1])[:total_cap]]
        logger.info("Topic search: %s unique repos (capped at %s)", len(full_names), total_cap)
        return await self._fetch_and_upsert_repos(full_names)

    async def _fetch_and_upsert_repos(self, full_names: list[str]) -> int:
        """Fetch each repo from API (or use cached DB row), upsert Repository and create TrendSnapshot."""
        settings = Settings()
        delay = settings.github_request_delay_seconds
        count = 0
        async with GitHubClient() as client:
            for i, full_name in enumerate(full_names):
                if delay > 0 and i > 0:
                    await asyncio.sleep(delay)
                try:
                    # Use persisted repo when fresh to avoid re-scraping GitHub
                    cached = await self._get_cached_repo(full_name)
                    if cached is not None:
                        await self._add_snapshot_from_cached_repo(cached)
                        await self.session.commit()
                        count += 1
                        logger.debug("Used cached repo: %s", full_name)
                        continue
                    parts = full_name.split("/", 1)
                    if len(parts) != 2:
                        continue
                    owner, name = parts
                    repo_data = await client.get_repo(owner, name)
                    if not repo_data or repo_data.get("id") is None:
                        continue
                    await self._upsert_repo_and_snapshot(client, repo_data)
                    await self.session.commit()
                    count += 1
                except Exception as e:
                    logger.warning("Failed to process %s: %s", full_name, e)
        return count

    async def _upsert_repo_and_snapshot(self, client: GitHubClient, repo_data: dict[str, Any]) -> None:
        """Upsert one repository and append a trend snapshot."""
        row = _repo_from_api(repo_data)
        github_id = row["github_id"]
        full_name = row["full_name"]
        owner = row["owner"]
        name = row["name"]

        # Optional: README and languages (cost extra requests)
        try:
            content_b64, encoding = await client.get_readme(owner, name)
            if content_b64:
                decoded = _decode_readme(content_b64, encoding)
                if decoded:
                    row["has_readme"] = True
                    row["readme_content"] = decoded[:README_MAX_CHARS] if len(decoded) > README_MAX_CHARS else decoded
        except Exception:
            pass
        try:
            langs = await client.get_languages(owner, name)
            if langs:
                row["languages_json"] = langs
        except Exception:
            pass

        # Upsert repository
        ins = pg_insert(Repository).values(**row)
        excl = ins.excluded
        stmt = ins.on_conflict_do_update(
            index_elements=[Repository.github_id],
            set_={
                Repository.full_name: excl.full_name,
                Repository.owner: excl.owner,
                Repository.name: excl.name,
                Repository.description: excl.description,
                Repository.html_url: excl.html_url,
                Repository.homepage_url: excl.homepage_url,
                Repository.primary_language: excl.primary_language,
                Repository.languages_json: excl.languages_json,
                Repository.topics: excl.topics,
                Repository.license_spdx: excl.license_spdx,
                Repository.has_readme: excl.has_readme,
                Repository.readme_content: excl.readme_content,
                Repository.stars_count: excl.stars_count,
                Repository.forks_count: excl.forks_count,
                Repository.open_issues_count: excl.open_issues_count,
                Repository.watchers_count: excl.watchers_count,
                Repository.default_branch: excl.default_branch,
                Repository.pushed_at_gh: excl.pushed_at_gh,
                Repository.is_fork: excl.is_fork,
                Repository.is_archived: excl.is_archived,
                Repository.is_mirror: excl.is_mirror,
                Repository.updated_at: datetime.now(timezone.utc),
            },
        )
        await self.session.execute(stmt)
        await self.session.flush()

        # Get repository_id for snapshot (we need it after upsert)
        result = await self.session.execute(select(Repository.id).where(Repository.github_id == github_id))
        repo_id = result.scalar_one()

        # Deltas: compare to previous snapshots
        prev = await self.session.execute(
            select(TrendSnapshot)
            .where(TrendSnapshot.repository_id == repo_id)
            .order_by(TrendSnapshot.snapshot_at.desc())
            .limit(2)
        )
        prev_snapshots = list(prev.scalars().all())
        stars_delta_1h: int | None = None
        stars_delta_24h: int | None = None
        forks_delta_24h: int | None = None
        if len(prev_snapshots) >= 1:
            stars_delta_1h = row["stars_count"] - prev_snapshots[0].stars_count
        if len(prev_snapshots) >= 2:
            stars_delta_24h = row["stars_count"] - prev_snapshots[1].stars_count
            forks_delta_24h = row["forks_count"] - prev_snapshots[1].forks_count

        # commits_7d from commit_activity (optional)
        commits_7d: int | None = None
        try:
            activity = await client.get_commit_activity(owner, name)
            if activity:
                commits_7d = sum(w.get("total", 0) or 0 for w in activity[-2:])  # last 2 weeks approx
        except Exception:
            pass

        snapshot = TrendSnapshot(
            repository_id=repo_id,
            stars_count=row["stars_count"],
            forks_count=row["forks_count"],
            open_issues_count=row["open_issues_count"],
            watchers_count=row["watchers_count"],
            stars_delta_1h=stars_delta_1h,
            stars_delta_24h=stars_delta_24h,
            forks_delta_24h=forks_delta_24h,
            commits_7d=commits_7d,
        )
        self.session.add(snapshot)

    async def reset_all_repo_data(self) -> int:
        """Delete all repositories (and cascade to trend_snapshots, repository_categories, generated_content, repo_embeddings).
        Use this to start from scratch so the next pipeline run inserts fresh data and stats (tracked / added today) update.
        Leaves categories table intact. Returns number of repositories deleted."""
        from sqlalchemy import delete

        result = await self.session.execute(delete(Repository))
        await self.session.commit()
        return result.rowcount or 0

    async def cleanup_old_snapshots(self, older_than_days: int = 30) -> int:
        """Delete trend_snapshots older than given days. Returns deleted count."""
        from sqlalchemy import delete

        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        result = await self.session.execute(delete(TrendSnapshot).where(TrendSnapshot.snapshot_at < cutoff))
        await self.session.commit()
        return result.rowcount or 0
