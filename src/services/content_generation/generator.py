"""Generate one content type for a repo via LLM and persist to generated_content."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.content import GeneratedContent
from src.models.repository import Repository
from src.services.content_generation.prompts import CONTENT_PROMPTS, PROMPT_VERSION, SYSTEM

logger = logging.getLogger(__name__)

README_EXCERPT_LEN = 2000


def _excerpt(s: str | None) -> str:
    return (s or "")[:README_EXCERPT_LEN]


def _topics_str(topics: list | None) -> str:
    if not topics:
        return ""
    return ", ".join(str(t) for t in topics[:20])


async def generate_one(
    session: AsyncSession,
    repo: Repository,
    content_type: str,
    llm,
) -> GeneratedContent | None:
    """Generate one content type for repo, insert into generated_content. Returns the row or None."""
    template = CONTENT_PROMPTS.get(content_type)
    if not template:
        return None
    user_prompt = template.format(
        full_name=repo.full_name,
        description=repo.description or "",
        primary_language=repo.primary_language or "",
        topics=_topics_str(repo.topics),
        readme_excerpt=_excerpt(repo.readme_content),
    )
    try:
        response = await llm.generate(SYSTEM, user_prompt, max_tokens=2048, temperature=0.3)
    except Exception as e:
        logger.warning("LLM generate failed for %s %s: %s", repo.full_name, content_type, e)
        return None
    usage = response.usage
    token_usage = {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_cost_usd": usage.total_cost_usd,
    }
    ins = pg_insert(GeneratedContent).values(
        repository_id=repo.id,
        content_type=content_type,
        content_markdown=response.content,
        llm_provider=response.provider,
        llm_model=response.model,
        prompt_version=PROMPT_VERSION,
        token_usage=token_usage,
    )
    stmt = ins.on_conflict_do_update(
        index_elements=["repository_id", "content_type", "prompt_version"],
        set_={
            GeneratedContent.content_markdown: ins.excluded.content_markdown,
            GeneratedContent.llm_provider: ins.excluded.llm_provider,
            GeneratedContent.llm_model: ins.excluded.llm_model,
            GeneratedContent.token_usage: ins.excluded.token_usage,
        },
    )
    await session.execute(stmt)
    await session.flush()
    result = await session.execute(
        select(GeneratedContent).where(
            GeneratedContent.repository_id == repo.id,
            GeneratedContent.content_type == content_type,
            GeneratedContent.prompt_version == PROMPT_VERSION,
        )
    )
    return result.scalar_one_or_none()
