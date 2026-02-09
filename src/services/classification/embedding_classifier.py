"""Category confidence via pgvector cosine similarity (repo embedding vs category profile embedding)."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.llm import embeddings as emb
from src.models.category import Category
from src.models.embedding import RepoEmbedding
from src.models.repository import Repository

logger = logging.getLogger(__name__)

# Weight: 0.4 embedding, 0.35 keyword, 0.25 language per spec
W_EMBEDDING = 0.4
W_KEYWORD = 0.35
W_LANGUAGE = 0.25
MIN_COMBINED = 0.3


def _source_hash(readme: str | None) -> str:
    return hashlib.sha256((readme or "").encode()).hexdigest()


async def ensure_repo_embedding(session: AsyncSession, repo: Repository) -> RepoEmbedding | None:
    """Create or reuse repo_embedding for README. Returns None if no README."""
    if not repo.readme_content:
        return None
    source_hash = _source_hash(repo.readme_content)
    existing = await session.execute(
        select(RepoEmbedding).where(RepoEmbedding.repository_id == repo.id)
    )
    row = existing.scalar_one_or_none()
    from src.config import Settings
    settings = Settings()
    model = settings.embedding_model
    if row and row.source_text_hash == source_hash:
        return row
    vec = await emb.embed_text(repo.readme_content)
    if row:
        row.embedding = vec
        row.source_text_hash = source_hash
        row.embedding_model = model
        return row
    new_row = RepoEmbedding(
        repository_id=repo.id,
        embedding=vec,
        embedding_model=model,
        source_text_hash=source_hash,
    )
    session.add(new_row)
    await session.flush()
    return new_row


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity in [0, 1] for normalized vectors; clamp to 0-1."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na <= 0 or nb <= 0:
        return 0.0
    sim = dot / (na * nb)
    return max(0.0, min(1.0, (sim + 1) / 2))


async def embedding_confidences_for_repo(
    session: AsyncSession,
    repo: Repository,
    categories: list[Category],
    repo_embedding: RepoEmbedding | None,
) -> dict[int, float]:
    """
    Return {category_id: confidence} using cosine similarity between repo embedding
    and category profile (name + description + keywords) embedding.
    """
    if not repo_embedding:
        return {c.id: 0.0 for c in categories}
    repo_vec = repo_embedding.embedding
    if not isinstance(repo_vec, list):
        repo_vec = list(repo_vec) if hasattr(repo_vec, "__iter__") else []
    out: dict[int, float] = {}
    for cat in categories:
        profile = f"{cat.name}. {cat.description or ''}. {' '.join(cat.keywords or [])}"
        cat_vec = await emb.embed_text(profile)
        out[cat.id] = cosine_similarity(repo_vec, cat_vec)
    return out
