#!/usr/bin/env -S python3
"""Seed categories. Run once after migrations. Uses CATEGORIES from env (JSON) or defaults from constants."""

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


async def seed() -> None:
    settings = Settings()
    categories = settings.categories
    source = "env (CATEGORIES)" if (settings.categories_json and settings.categories_json.strip()) else "constants"
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        for i, cat in enumerate(categories, start=1):
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
    slugs = [c["slug"] for c in categories]
    print(f"Seeded {len(categories)} categories from {source}: {slugs}")


if __name__ == "__main__":
    asyncio.run(seed())
