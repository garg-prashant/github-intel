#!/usr/bin/env -S python3
"""Run ingestion once (trending and/or search). For verification and manual runs."""

import argparse
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import session_scope
from src.services.trend_ingestion.service import TrendIngestionService


async def run_trending() -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.ingest_from_trending_pages()


async def run_search() -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.ingest_from_search_api()


async def run_cleanup(days: int = 30) -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.cleanup_old_snapshots(older_than_days=days)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ingestion (trending, search, cleanup)")
    parser.add_argument("--trending", action="store_true", help="Scrape trending and upsert repos")
    parser.add_argument("--search", action="store_true", help="Run search API per category and upsert")
    parser.add_argument("--cleanup", action="store_true", help="Delete snapshots older than 30 days")
    parser.add_argument("--cleanup-days", type=int, default=30, help="Cleanup snapshots older than N days")
    args = parser.parse_args()

    if not (args.trending or args.search or args.cleanup):
        parser.error("At least one of --trending, --search, --cleanup required")

    if args.trending:
        n = asyncio.run(run_trending())
        print(f"Trending ingestion: {n} repos processed")
    if args.search:
        n = asyncio.run(run_search())
        print(f"Search ingestion: {n} repos processed")
    if args.cleanup:
        n = asyncio.run(run_cleanup(args.cleanup_days))
        print(f"Cleanup: {n} snapshots deleted")


if __name__ == "__main__":
    main()
