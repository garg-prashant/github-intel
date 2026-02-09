"""Trending page HTML scraper — BeautifulSoup parser for github.com/trending."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TRENDING_BASE = "https://github.com/trending"
SINCE_OPTIONS = ("daily", "weekly")
LANGUAGE_OPTIONS = ("", "python", "typescript", "rust", "go")
USER_AGENT = "github-intel-ingestion/1.0"
REQUEST_TIMEOUT = 25.0


def _normalize_full_name(link_text: str) -> str | None:
    """Extract 'owner/repo' from link href (e.g. /owner/repo or /owner/repo?other=1)."""
    link_text = link_text.strip().lstrip("/")
    if not link_text:
        return None
    parts = link_text.split("?")[0].split("/")
    if len(parts) >= 2 and parts[0] and parts[1]:
        return f"{parts[0]}/{parts[1]}"
    return None


def parse_trending_html(html: str) -> list[str]:
    """Parse trending page HTML; return list of repo full_name (owner/repo)."""
    soup = BeautifulSoup(html, "html.parser")
    full_names: list[str] = []
    seen: set[str] = set()
    for article in soup.select('article.Box-row'):
        # h2 contains <a href="/owner/repo"> or similar
        h2 = article.select_one("h2")
        if not h2:
            continue
        a = h2.select_one("a")
        if not a or not a.get("href"):
            continue
        name = _normalize_full_name(a["href"])
        if name and name not in seen:
            seen.add(name)
            full_names.append(name)
    return full_names


async def fetch_trending_page(since: str = "daily", language: str = "") -> str:
    """Fetch raw HTML for one trending view."""
    params: dict[str, str] = {"since": since}
    if language:
        params["language"] = language
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        r = await client.get(
            TRENDING_BASE,
            params=params,
            headers={"User-Agent": USER_AGENT},
        )
        r.raise_for_status()
        return r.text


def scrape_trending_full_names_sync(html: str) -> list[str]:
    """Sync wrapper for parse_trending_html (same logic)."""
    return parse_trending_html(html)


async def scrape_trending_full_names(
    since_options: tuple[str, ...] = SINCE_OPTIONS,
    language_options: tuple[str, ...] = LANGUAGE_OPTIONS,
) -> list[str]:
    """
    Scrape all configured trending views and return unique repo full names.
    Uses daily/weekly and multiple languages.
    """
    seen: set[str] = set()
    for since in since_options:
        for language in language_options:
            try:
                html = await fetch_trending_page(since=since, language=language)
                names = parse_trending_html(html)
                for n in names:
                    seen.add(n)
            except Exception as e:
                logger.warning("Trending scrape failed since=%s language=%s: %s", since, language or "(all)", e)
    return list(seen)
