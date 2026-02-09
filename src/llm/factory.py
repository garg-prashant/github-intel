"""LLM provider factory from settings."""

from __future__ import annotations

from src.config import Settings
from src.llm.base import LLMProvider
from src.llm.openai_provider import OpenAIProvider
from src.llm.anthropic_provider import AnthropicProvider


def create_llm(settings: Settings | None = None) -> LLMProvider:
    if settings is None:
        settings = Settings()
    if settings.llm_provider == "anthropic":
        return AnthropicProvider()
    return OpenAIProvider()
