"""Pipeline control: trigger ingestion → scoring → classification → content on demand.

When you run the pipeline (POST /pipeline/run), a Celery chain runs four steps in order:
  1. Ingest topic search — GitHub search by topics (AI, agent, MCP, crypto), languages (Go, Python, TypeScript, JavaScript).
  2. Score & filter — compute trend score, set quality_passed on repos that pass filters.
  3. Classify — keyword + embedding + language → assign repository_categories.
  4. Generate content — LLM generates learning content for top repos per category.

Use ?reset_first=true to clear all repo data (repos, snapshots, content, etc.) before running, so tracked/added counts reflect the new run.
See LOCAL_SETUP.md "How the pipeline works" for details.
"""

from fastapi import APIRouter, Body, HTTPException, Query
from celery import chain
from pydantic import BaseModel

from src.celery_app import celery
from src.config import Settings
from src.database import session_scope
from src.services.trend_ingestion.service import TrendIngestionService
from src.tasks.ingestion_tasks import ingest_topic_search_repos
from src.tasks.scoring_tasks import score_and_filter_all_task
from src.tasks.classification_tasks import classify_new_repos_task
from src.tasks.content_tasks import generate_content_for_top_repos_task

router = APIRouter()

PIPELINE_STEP_NAMES = [
    "Ingest topic search",
    "Score & filter",
    "Classify",
    "Generate content",
]


class PipelineRunBody(BaseModel):
    """Optional body for POST /pipeline/run. Restrict ingestion to these category slugs (uses each category's search_topic)."""

    categories: list[str] | None = None


class PipelineTriggerResponse(BaseModel):
    started: bool
    message: str
    chain_id: str | None = None


class PipelineResetResponse(BaseModel):
    deleted: int
    message: str


class PipelineStepStatus(BaseModel):
    name: str
    status: str  # "pending" | "running" | "success" | "failure"


class PipelineStatusResponse(BaseModel):
    chain_id: str
    status: str  # "running" | "success" | "failure"
    current_step_index: int | None  # 0..4 when running, null when done
    steps: list[PipelineStepStatus]
    error: str | None = None


def _collect_chain_results(chain_id: str) -> list:
    """Walk from last task (chain_id) back to root via .parent, return [first, ..., last].
    When using Redis result backend, .parent is often not restored from storage, so we
    typically get only the last task (chain head). Caller handles both 1 and 5 results.
    """
    result = celery.AsyncResult(chain_id)
    results = []
    while result is not None:
        results.append(result)
        parent = getattr(result, "parent", None)
        result = parent if parent else None
    results.reverse()
    return results


async def _reset_all_repo_data() -> int:
    async with session_scope() as session:
        svc = TrendIngestionService(session)
        return await svc.reset_all_repo_data()


@router.post("/pipeline/reset", response_model=PipelineResetResponse)
async def reset_data() -> PipelineResetResponse:
    """Clear all repo data (repos, snapshots, content, embeddings). Use before running the pipeline to start from scratch."""
    deleted = await _reset_all_repo_data()
    return PipelineResetResponse(
        deleted=deleted,
        message=f"Cleared {deleted} repositories and related data.",
    )


def _topic_terms_for_categories(category_slugs: list[str]) -> list[str]:
    """Resolve category slugs to GitHub topic search terms from configured categories (search_topic)."""
    settings = Settings()
    slug_to_topic: dict[str, str] = {}
    for cat in settings.categories:
        slug = cat.get("slug")
        topic = cat.get("search_topic")
        if isinstance(slug, str) and isinstance(topic, str):
            slug_to_topic[slug] = topic
    terms: list[str] = []
    seen: set[str] = set()
    for slug in category_slugs:
        t = slug_to_topic.get(slug)
        if t and t not in seen:
            terms.append(t)
            seen.add(t)
    return terms


@router.post("/pipeline/run", response_model=PipelineTriggerResponse)
async def trigger_pipeline(
    reset_first: bool = Query(False, description="Clear all repo data before running so tracked/added counts reflect this run"),
    body: PipelineRunBody | None = Body(None),
) -> PipelineTriggerResponse:
    """Run the full pipeline on demand: ingest (topic search) → score → classify → content.
    Set reset_first=true to delete all repositories and related data first (start from scratch).
    Optionally pass body with categories: list of slugs to scrape only those (uses each category's search_topic)."""
    if reset_first:
        deleted = await _reset_all_repo_data()
        message = f"Cleared {deleted} repositories. Pipeline started: ingest → score → classify → content."
    else:
        message = "Pipeline started. Tasks run in order: ingest topic search → score → classify → generate content."
    topic_terms: list[str] | None = None
    if body and body.categories:
        topic_terms = _topic_terms_for_categories(body.categories)
        if topic_terms:
            message += f" Ingestion limited to topics: {', '.join(topic_terms)}."
    # Use .si() (immutable) so each task gets no args; otherwise chain passes previous result as first arg
    first_task = ingest_topic_search_repos.si(topic_terms=topic_terms) if topic_terms else ingest_topic_search_repos.si()
    workflow = chain(
        first_task,
        score_and_filter_all_task.si(),
        classify_new_repos_task.si(),
        generate_content_for_top_repos_task.si(),
    )
    result = workflow.apply_async()
    return PipelineTriggerResponse(
        started=True,
        message=message,
        chain_id=result.id,
    )


@router.get("/pipeline/status/{chain_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(chain_id: str) -> PipelineStatusResponse:
    """Return current pipeline progress: which step is running and each step's status.
    When the result backend (e.g. Redis) does not restore chain parent links, we get
    only the last task; we then infer overall status from that and show N steps with
    the last step reflecting the known state.
    """
    try:
        results = _collect_chain_results(chain_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid chain id or backend unavailable: {e}") from e

    if not results:
        raise HTTPException(status_code=400, detail="No task found for this chain id.")

    steps: list[PipelineStepStatus] = []
    current_index: int | None = None
    overall = "running"
    error: str | None = None

    # Redis (and some backends) don't store .parent, so we often get only the last task.
    if len(results) != len(PIPELINE_STEP_NAMES):
        # Single result = chain head (last task). Map its state to last step; earlier steps unknown.
        r = results[0]
        state = (r.state or "PENDING").upper()
        if state == "SUCCESS":
            for name in PIPELINE_STEP_NAMES:
                steps.append(PipelineStepStatus(name=name, status="success"))
            overall = "success"
        elif state == "FAILURE":
            for i, name in enumerate(PIPELINE_STEP_NAMES):
                steps.append(
                    PipelineStepStatus(name=name, status="failure" if i == len(PIPELINE_STEP_NAMES) - 1 else "pending")
                )
            overall = "failure"
            current_index = len(PIPELINE_STEP_NAMES) - 1
            try:
                error = str(r.result) if r.result else "Task failed"
            except Exception:
                error = "Task failed"
        elif state in ("STARTED", "RETRY"):
            for i, name in enumerate(PIPELINE_STEP_NAMES):
                steps.append(
                    PipelineStepStatus(name=name, status="running" if i == len(PIPELINE_STEP_NAMES) - 1 else "pending")
                )
            current_index = len(PIPELINE_STEP_NAMES) - 1
        else:
            for i, name in enumerate(PIPELINE_STEP_NAMES):
                steps.append(PipelineStepStatus(name=name, status="pending"))
            current_index = len(PIPELINE_STEP_NAMES) - 1
    else:
        for i, r in enumerate(results):
            state = (r.state or "PENDING").upper()
            if state == "SUCCESS":
                steps.append(PipelineStepStatus(name=PIPELINE_STEP_NAMES[i], status="success"))
            elif state == "FAILURE":
                steps.append(PipelineStepStatus(name=PIPELINE_STEP_NAMES[i], status="failure"))
                if current_index is None:
                    current_index = i
                if overall == "running":
                    overall = "failure"
                    try:
                        error = str(r.result) if r.result else "Task failed"
                    except Exception:
                        error = "Task failed"
            elif state in ("STARTED", "RETRY"):
                steps.append(PipelineStepStatus(name=PIPELINE_STEP_NAMES[i], status="running"))
                if current_index is None:
                    current_index = i
            else:
                steps.append(PipelineStepStatus(name=PIPELINE_STEP_NAMES[i], status="pending"))
                if current_index is None:
                    current_index = i

        if all(s.status == "success" for s in steps):
            overall = "success"
            current_index = None
        elif overall != "failure" and current_index is not None and steps[current_index].status == "running":
            pass
        elif overall != "failure" and current_index is not None:
            pass
        elif overall != "failure":
            if current_index is None:
                current_index = 0

    return PipelineStatusResponse(
        chain_id=chain_id,
        status=overall,
        current_step_index=current_index,
        steps=steps,
        error=error,
    )
