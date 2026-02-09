"""Pipeline control: trigger ingestion → scoring → classification → content on demand.

When you run the pipeline (POST /pipeline/run), a Celery chain runs five steps in order:
  1. Ingest trending — scrape github.com/trending, fetch repo/README/languages/activity from GitHub API.
  2. Ingest search — per-category search, fetch same metadata (capped per category).
  3. Score & filter — compute trend score, set quality_passed on repos that pass filters.
  4. Classify — keyword + embedding + language → assign repository_categories.
  5. Generate content — LLM generates learning content for top repos per category.

See LOCAL_SETUP.md "How the pipeline works" for details.
"""

from fastapi import APIRouter, HTTPException
from celery import chain
from pydantic import BaseModel

from src.celery_app import celery
from src.tasks.ingestion_tasks import ingest_trending_repos, ingest_search_api_repos
from src.tasks.scoring_tasks import score_and_filter_all_task
from src.tasks.classification_tasks import classify_new_repos_task
from src.tasks.content_tasks import generate_content_for_top_repos_task

router = APIRouter()

PIPELINE_STEP_NAMES = [
    "Ingest trending",
    "Ingest search",
    "Score & filter",
    "Classify",
    "Generate content",
]


class PipelineTriggerResponse(BaseModel):
    started: bool
    message: str
    chain_id: str | None = None


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


@router.post("/pipeline/run", response_model=PipelineTriggerResponse)
async def trigger_pipeline() -> PipelineTriggerResponse:
    """Run the full pipeline on demand: ingest (trending + search) → score → classify → content."""
    # Use .si() (immutable) so each task gets no args; otherwise chain passes previous result as first arg
    workflow = chain(
        ingest_trending_repos.si(),
        ingest_search_api_repos.si(),
        score_and_filter_all_task.si(),
        classify_new_repos_task.si(),
        generate_content_for_top_repos_task.si(),
    )
    result = workflow.apply_async()
    return PipelineTriggerResponse(
        started=True,
        message="Pipeline started. Tasks run in order: ingest trending → ingest search → score → classify → generate content.",
        chain_id=result.id,
    )


@router.get("/pipeline/status/{chain_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(chain_id: str) -> PipelineStatusResponse:
    """Return current pipeline progress: which step is running and each step's status.
    When the result backend (e.g. Redis) does not restore chain parent links, we get
    only the last task; we then infer overall status from that and show 5 steps with
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
        # Single result = chain head (last task). Map its state to step 5; steps 1–4 unknown.
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
