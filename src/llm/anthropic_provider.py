"""Anthropic LLM provider (claude-sonnet)."""

from __future__ import annotations

import time
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from src.config import Settings
from src.llm.base import LLMResponse, TokenUsage

ANTHROPIC_INPUT_COST_PER_1M = 3.0
ANTHROPIC_OUTPUT_COST_PER_1M = 15.0


@dataclass
class AnthropicProvider:
    provider_name: str = "anthropic"
    model_name: str = "claude-sonnet-4-20250514"

    def __post_init__(self) -> None:
        settings = Settings()
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model_name = getattr(settings, "anthropic_model", None) or self.model_name

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMResponse:
        start = time.perf_counter()
        r = await self._client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        latency_ms = int((time.perf_counter() - start) * 1000)
        content = ""
        if r.content:
            for block in r.content:
                if hasattr(block, "text"):
                    content += block.text
        pt = r.usage.input_tokens if r.usage else 0
        ct = r.usage.output_tokens if r.usage else 0
        cost = (pt / 1_000_000 * ANTHROPIC_INPUT_COST_PER_1M) + (ct / 1_000_000 * ANTHROPIC_OUTPUT_COST_PER_1M)
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
