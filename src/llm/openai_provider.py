"""OpenAI LLM provider (gpt-4o-mini)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from openai import AsyncOpenAI

from src.config import Settings
from src.llm.base import LLMResponse, TokenUsage


# Approximate $/1M tokens for gpt-4o-mini
OPENAI_INPUT_COST_PER_1M = 0.15
OPENAI_OUTPUT_COST_PER_1M = 0.60


@dataclass
class OpenAIProvider:
    provider_name: str = "openai"
    model_name: str = "gpt-4o-mini"

    def __post_init__(self) -> None:
        settings = Settings()
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model_name = settings.openai_model or self.model_name

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMResponse:
        start = time.perf_counter()
        r = await self._client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        choice = r.choices[0] if r.choices else None
        content = choice.message.content if choice else ""
        usage = r.usage
        pt = usage.prompt_tokens if usage else 0
        ct = usage.completion_tokens if usage else 0
        cost = (pt / 1_000_000 * OPENAI_INPUT_COST_PER_1M) + (ct / 1_000_000 * OPENAI_OUTPUT_COST_PER_1M)
        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model_name,
            usage=TokenUsage(
                prompt_tokens=pt,
                completion_tokens=ct,
                total_tokens=pt + ct,
                total_cost_usd=round(cost, 6),
            ),
            latency_ms=latency_ms,
        )
