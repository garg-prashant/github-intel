"""Embeddings: OpenAI (paid) or local sentence-transformers (free)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from src.config import Settings

logger = logging.getLogger(__name__)

# Dimensions per provider (OpenAI text-embedding-3-small vs all-MiniLM-L6-v2)
EMBEDDING_DIM_OPENAI = 1536
EMBEDDING_DIM_LOCAL = 384


def get_embedding_dim() -> int:
    """Return embedding dimension for current provider (1536 or 384)."""
    settings = Settings()
    return EMBEDDING_DIM_OPENAI if settings.embedding_provider == "openai" else EMBEDDING_DIM_LOCAL


def _embed_local_sync(model_name: str, texts: list[str], max_length: int = 8192) -> list[list[float]]:
    """Sync encode with sentence-transformers. Runs in thread. Uses CPU to avoid Metal/MPS
    crashes in forked Celery workers on macOS."""
    # Force CPU before any torch/sentence_transformers use. MPS (Metal) does not survive
    # process fork and causes SIGABRT (XPC_ERROR_CONNECTION_INVALID) in Celery workers.
    import torch
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        if hasattr(torch, "set_default_device"):
            torch.set_default_device("cpu")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise ImportError(
            "Local embeddings require sentence-transformers. Install with: pip install sentence-transformers"
            " (or set EMBEDDING_PROVIDER=openai to use OpenAI embeddings instead)"
        ) from e

    model = SentenceTransformer(model_name, device="cpu")
    truncated = [(t or " ")[:max_length] for t in texts]
    arr = model.encode(truncated, convert_to_numpy=True, normalize_embeddings=False)
    return arr.tolist()


async def embed_text(text: str) -> list[float]:
    """Return embedding vector for text. Provider and dimension from config."""
    settings = Settings()
    dim = get_embedding_dim()
    if not text or not text.strip():
        return [0.0] * dim

    if settings.embedding_provider == "local":
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(
            None,
            _embed_local_sync,
            settings.embedding_model,
            [text[:8192]],
        )
        return vectors[0] if vectors else [0.0] * dim

    # OpenAI
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY required for embeddings when embedding_provider=openai")
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    r = await client.embeddings.create(
        model=settings.embedding_model,
        input=text[:8192],
    )
    return r.data[0].embedding


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch embed; returns list of vectors (dimension from config)."""
    if not texts:
        return []
    settings = Settings()
    dim = get_embedding_dim()

    if settings.embedding_provider == "local":
        loop = asyncio.get_event_loop()
        inputs = [t[:8192] if t else " " for t in texts]
        return await loop.run_in_executor(
            None,
            _embed_local_sync,
            settings.embedding_model,
            inputs,
        )

    # OpenAI
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY required for embeddings when embedding_provider=openai")
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    inputs = [t[:8192] if t else " " for t in texts]
    r = await client.embeddings.create(model=settings.embedding_model, input=inputs)
    by_idx: dict[int, list[float]] = {d.index: d.embedding for d in r.data}
    return [by_idx.get(i, [0.0] * dim) for i in range(len(texts))]
