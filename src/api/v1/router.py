"""V1 API router — mounts all v1 endpoints."""

from fastapi import APIRouter

from src.api.v1 import health, trending, repositories, categories, stats, pipeline

api_router = APIRouter()
api_router.include_router(health.router, prefix="", tags=["health"])
api_router.include_router(trending.router, prefix="", tags=["trending"])
api_router.include_router(repositories.router, prefix="", tags=["repositories"])
api_router.include_router(categories.router, prefix="", tags=["categories"])
api_router.include_router(stats.router, prefix="", tags=["stats"])
api_router.include_router(pipeline.router, prefix="", tags=["pipeline"])
