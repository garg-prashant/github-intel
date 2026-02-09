#!/usr/bin/env -S python3
"""Run ingestion once (topic search, optional trending, cleanup). For verification and manual runs."""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import session_scope
from src.services.trend_ingestion.service import TrendIngestionService


async def run_topic_search() -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.ingest_from_topic_search()


async def run_trending() -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.ingest_from_trending_pages()


async def run_search() -> int:
    """Same as topic search (legacy --search flag)."""
    return await run_topic_search()


async def run_cleanup(days: int = 30) -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.cleanup_old_snapshots(older_than_days=days)


async def run_reset() -> int:
    """Delete all repos (and cascaded data). Use before ingestion to start from scratch so stats update."""
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.reset_all_repo_data()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ingestion (topic search, optional trending, cleanup)")
    parser.add_argument("--reset", action="store_true", help="Clear all repo data first (repos, snapshots, content, etc.). Use with --topic to start from scratch so tracked/added counts reflect the run.")
    parser.add_argument("--topic", action="store_true", help="Topic search (AI, agent, MCP, crypto), languages Go/Python/TS/JS")
    parser.add_argument("--search", action="store_true", help="Same as --topic (legacy)")
    parser.add_argument("--trending", action="store_true", help="Scrape github.com/trending (legacy)")
    parser.add_argument("--cleanup", action="store_true", help="Delete snapshots older than 30 days")
    parser.add_argument("--cleanup-days", type=int, default=30, help="Cleanup snapshots older than N days")
    args = parser.parse_args()

    if not (args.reset or args.topic or args.search or args.trending or args.cleanup):
        parser.error("At least one of --reset, --topic, --search, --trending, --cleanup required")

    if args.reset:
        n = asyncio.run(run_reset())
        print(f"Reset: {n} repositories (and related data) deleted.")
        if not (args.topic or args.search or args.trending):
            print("Run with --topic (or trigger the pipeline) to re-ingest and see updated counts.")

    if args.topic or args.search:
        n = asyncio.run(run_topic_search())
        print(f"Topic search ingestion: {n} repos processed")
    if args.trending:
        n = asyncio.run(run_trending())
        print(f"Trending ingestion: {n} repos processed")
    if args.cleanup:
        n = asyncio.run(run_cleanup(args.cleanup_days))
        print(f"Cleanup: {n} snapshots deleted")


if __name__ == "__main__":
    main()
