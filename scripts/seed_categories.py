#!/usr/bin/env -S python3
"""Seed the 7 static categories. Run once after migrations."""

from __future__ import annotations

import asyncio
import json
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.config import Settings
from src.models.base import Base
from src.models import *  # noqa: F401, F403


CATEGORIES = [
    {
        "slug": "ai-ml",
        "name": "AI & Machine Learning",
        "description": "Machine learning frameworks, training, and inference tooling",
        "keywords": ["pytorch", "tensorflow", "neural", "machine learning", "deep learning", "training", "inference", "transformers"],
    },
    {
        "slug": "llms-agents",
        "name": "LLMs & Agents",
        "description": "Large language models, agents, RAG, and orchestration",
        "keywords": ["llm", "agent", "RAG", "retrieval", "langchain", "openai", "anthropic", "orchestration", "prompt"],
    },
    {
        "slug": "mcp-tooling",
        "name": "MCP & Tooling",
        "description": "Model Context Protocol, MCP servers, and AI tooling",
        "keywords": ["mcp", "model context protocol", "mcp server", "tool", "plugin"],
    },
    {
        "slug": "backend",
        "name": "Backend",
        "description": "API frameworks, services, and backend infrastructure",
        "keywords": ["api", "backend", "framework", "rest", "graphql", "server", "microservice"],
    },
    {
        "slug": "python-libs",
        "name": "Python Libraries",
        "description": "Popular Python libraries and utilities",
        "keywords": ["python", "library", "package", "pip", "pypi"],
    },
    {
        "slug": "web3-crypto",
        "name": "Web3 & Crypto",
        "description": "Blockchain, smart contracts, and crypto tooling",
        "keywords": ["blockchain", "ethereum", "smart contract", "web3", "crypto", "defi", "solidity"],
    },
    {
        "slug": "devops-mlops",
        "name": "DevOps & MLOps",
        "description": "CI/CD, deployment, and ML operations",
        "keywords": ["devops", "mlops", "ci/cd", "deploy", "kubernetes", "docker", "pipeline", "monitoring"],
    },
]


async def seed() -> None:
    settings = Settings()
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for i, cat in enumerate(CATEGORIES, start=1):
            await session.execute(
                text("""
                INSERT INTO categories (id, slug, name, description, keywords)
                VALUES (:id, :slug, :name, :description, :keywords)
                ON CONFLICT (slug) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    keywords = EXCLUDED.keywords
                """),
                {
                    "id": i,
                    "slug": cat["slug"],
                    "name": cat["name"],
                    "description": cat["description"],
                    "keywords": json.dumps(cat["keywords"]),
                },
            )
        await session.commit()
    await engine.dispose()
    print(f"Seeded {len(CATEGORIES)} categories.")


if __name__ == "__main__":
    asyncio.run(seed())
