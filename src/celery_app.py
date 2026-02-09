"""Celery instance. Pipeline runs on-demand only (no cron); results are stored for the next run."""

from celery import Celery
from celery.signals import worker_process_init

from src.config import Settings


@worker_process_init.connect
def _force_cpu_in_worker(**kwargs):
    """Force PyTorch to use CPU in each forked worker. MPS (Metal) does not survive fork
    and causes SIGABRT (XPC_ERROR_CONNECTION_INVALID) when using sentence-transformers."""
    try:
        import torch
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            if hasattr(torch, "set_default_device"):
                torch.set_default_device("cpu")
    except Exception:
        pass

settings = Settings()
celery = Celery(
    "github_intel",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "src.tasks.ingestion_tasks",
        "src.tasks.scoring_tasks",
        "src.tasks.classification_tasks",
        "src.tasks.content_tasks",
    ],
)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_routes={
        "src.tasks.ingestion_tasks.*": {"queue": "ingestion"},
        "src.tasks.scoring_tasks.*": {"queue": "scoring"},
        "src.tasks.classification_tasks.*": {"queue": "classification"},
        "src.tasks.content_tasks.*": {"queue": "content"},
    },
    beat_schedule={},  # No cron; pipeline is triggered on-demand via POST /api/v1/pipeline/run
)
