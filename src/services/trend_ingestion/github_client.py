"""Async GitHub API client with rate-limit tracking, retry, and semaphore-based concurrency."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from src.config import Settings

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"
CORE_LOW_THRESHOLD = 50
SEARCH_LOW_THRESHOLD = 1
MAX_CONCURRENT = 5
RETRY_STATUSES = (403, 429)
INITIAL_BACKOFF = 60
MAX_BACKOFF = 600


class GitHubClient:
    """Async httpx client for GitHub API with rate-limit handling and retries."""

    def __init__(
        self,
        token: str | None = None,
        max_concurrent: int = MAX_CONCURRENT,
    ) -> None:
        settings = Settings()
        self._token = token or settings.github_token
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._core_remaining: int | None = None
        self._core_reset: int | None = None
        self._search_remaining: int | None = None
        self._search_reset: int | None = None
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "GitHubClient":
        headers: dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "github-intel-ingestion",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        self._client = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers=headers,
            timeout=30.0,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    def _update_rate_limits(self, response: httpx.Response) -> None:
        def parse_int(name: str) -> int | None:
            v = response.headers.get(name)
            return int(v) if v is not None else None

        self._core_remaining = parse_int("x-ratelimit-remaining")
        self._core_reset = parse_int("x-ratelimit-reset")
        # Search has its own limit; same headers but for search endpoint
        if "/search/" in str(response.request.url):
            self._search_remaining = parse_int("x-ratelimit-remaining")
            self._search_reset = parse_int("x-ratelimit-reset")

    async def _wait_if_low_limit(self, is_search: bool) -> None:
        remaining = self._search_remaining if is_search else self._core_remaining
        reset = self._search_reset if is_search else self._core_reset
        threshold = SEARCH_LOW_THRESHOLD if is_search else CORE_LOW_THRESHOLD
        if remaining is not None and remaining < threshold and reset is not None:
            wait = max(0, reset - int(time.time())) + 5
            if wait > 0:
                logger.warning("Rate limit low (%s): sleeping %ds", "search" if is_search else "core", wait)
                await asyncio.sleep(min(wait, 300))

    async def _request(
        self,
        method: str,
        path: str,
        *,
        is_search: bool = False,
        **kwargs: Any,
    ) -> httpx.Response:
        if not self._client:
            raise RuntimeError("Client not started; use async with GitHubClient()")
        await self._semaphore.acquire()
        try:
            await self._wait_if_low_limit(is_search)
            response = await self._client.request(method, path, **kwargs)
            self._update_rate_limits(response)
            return response
        finally:
            self._semaphore.release()

    async def get_with_retry(
        self,
        path: str,
        *,
        is_search: bool = False,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> httpx.Response:
        backoff = INITIAL_BACKOFF
        for attempt in range(max_retries + 1):
            response = await self._request("GET", path, is_search=is_search, **kwargs)
            if response.status_code not in RETRY_STATUSES:
                response.raise_for_status()
                return response
            if attempt == max_retries:
                response.raise_for_status()
                return response
            reset = self._core_reset or (int(time.time()) + 60)
            wait = max(backoff, reset - int(time.time()) + 5)
            logger.warning("GitHub rate limit (attempt %s): sleeping %ds", attempt + 1, wait)
            await asyncio.sleep(min(wait, MAX_BACKOFF))
            backoff = min(backoff * 2, MAX_BACKOFF)
        return response

    async def get_repo(self, owner: str, repo: str) -> dict[str, Any]:
        """GET /repos/{owner}/{repo}."""
        r = await self.get_with_retry(f"/repos/{owner}/{repo}")
        return r.json()

    async def get_readme(self, owner: str, repo: str) -> tuple[str | None, str | None]:
        """GET /repos/{owner}/{repo}/readme. Returns (content_base64_or_none, encoding)."""
        r = await self.get_with_retry(f"/repos/{owner}/{repo}/readme")
        if r.status_code == 404:
            return None, None
        r.raise_for_status()
        data = r.json()
        return data.get("content"), data.get("encoding")

    async def get_languages(self, owner: str, repo: str) -> dict[str, int] | None:
        """GET /repos/{owner}/{repo}/languages."""
        r = await self.get_with_retry(f"/repos/{owner}/{repo}/languages")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def get_commit_activity(self, owner: str, repo: str) -> list[dict[str, Any]] | None:
        """GET /repos/{owner}/{repo}/stats/commit_activity. Returns weekly activity or None."""
        r = await self.get_with_retry(f"/repos/{owner}/{repo}/stats/commit_activity")
        if r.status_code in (202, 204):
            return None
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()

    async def search_repositories(self, query: str, page: int = 1, per_page: int = 30) -> dict[str, Any]:
        """GET /search/repositories. Uses search rate limit."""
        r = await self.get_with_retry(
            "/search/repositories",
            params={"q": query, "page": page, "per_page": per_page, "sort": "stars"},
            is_search=True,
        )
        return r.json()
