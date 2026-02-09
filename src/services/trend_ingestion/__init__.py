"""Trend ingestion: GitHub client, scrapers, orchestration."""

from src.services.trend_ingestion.github_client import GitHubClient
from src.services.trend_ingestion.scrapers import scrape_trending_full_names
from src.services.trend_ingestion.service import TrendIngestionService

__all__ = ["GitHubClient", "scrape_trending_full_names", "TrendIngestionService"]
