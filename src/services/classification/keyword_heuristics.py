"""Keyword-based category confidence from README, topics, description."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import select

from src.models.category import Category
from src.models.repository import Repository


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower().strip())


def keyword_confidence(repo: Repository, category: Category) -> float:
    """
    Return 0.0-1.0 confidence based on keyword matches in repo topics, description, readme.
    Uses category.keywords (list of strings).
    """
    keywords = category.keywords or []
    if not keywords:
        return 0.0
    text_parts: list[str] = []
    if repo.topics:
        text_parts.extend(str(t) for t in repo.topics)
    if repo.description:
        text_parts.append(repo.description)
    if repo.readme_content:
        text_parts.append(repo.readme_content[:5000])
    combined = _normalize(" ".join(text_parts))
    if not combined:
        return 0.0
    matches = sum(1 for kw in keywords if _normalize(kw) in combined)
    if not keywords:
        return 0.0
    return min(1.0, matches / max(1, len(keywords) * 0.5))


async def keyword_confidences_for_repo(
    session: Any,
    repo: Repository,
    categories: list[Category],
) -> dict[int, float]:
    """Return {category_id: confidence} for all categories."""
    return {c.id: keyword_confidence(repo, c) for c in categories}
