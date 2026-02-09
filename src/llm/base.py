"""LLM provider protocol and response type."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class TokenUsage:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost_usd: float | None = None


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str
    usage: TokenUsage
    latency_ms: int


class LLMProvider(Protocol):
    provider_name: str
    model_name: str

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> LLMResponse:
        ...
