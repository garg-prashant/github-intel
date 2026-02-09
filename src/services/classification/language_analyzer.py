"""Language- and stack-based category confidence."""

from __future__ import annotations

import re
from typing import Any

from src.models.category import Category
from src.models.repository import Repository

# Map category slug to preferred languages / stack hints (optional boost)
CATEGORY_LANGUAGE_HINTS: dict[str, set[str]] = {
    "ai-ml": {"python", "julia", "r"},
    "llms-agents": {"python", "typescript"},
    "mcp-tooling": {"typescript", "python", "rust"},
    "backend": {"python", "go", "rust", "java", "typescript"},
    "python-libs": {"python"},
    "web3-crypto": {"solidity", "rust", "typescript", "go"},
    "devops-mlops": {"python", "go", "hcl"},
}


def _readme_lower(readme: str | None) -> str:
    return (readme or "").lower()


def language_confidence(repo: Repository, category: Category) -> float:
    """
    Return 0.0-1.0 based on primary_language, languages_json, and README dependency hints.
    """
    slug = category.slug
    hints = CATEGORY_LANGUAGE_HINTS.get(slug) or set()
    score = 0.0
    primary = (repo.primary_language or "").lower()
    if primary and primary in hints:
        score += 0.5
    langs = repo.languages_json or {}
    if isinstance(langs, dict):
        for lang in langs:
            if lang.lower() in hints:
                score += 0.2
                break
    readme = _readme_lower(repo.readme_content)
    if readme:
        if "requirements.txt" in readme or "pyproject.toml" in readme and slug in ("python-libs", "ai-ml", "backend"):
            score += 0.2
        if "package.json" in readme and slug in ("llms-agents", "mcp-tooling", "web3-crypto"):
            score += 0.2
        if "cargo.toml" in readme and slug in ("mcp-tooling", "backend", "web3-crypto"):
            score += 0.2
    return min(1.0, score)


async def language_confidences_for_repo(
    repo: Repository,
    categories: list[Category],
) -> dict[int, float]:
    """Return {category_id: confidence} for all categories."""
    return {c.id: language_confidence(repo, c) for c in categories}
