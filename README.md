# GitHub Trending Intelligence

Discover trending GitHub repositories, score them, classify by domain, and generate learning content via LLM. Served through a web UI.

**Stack:** Python 3.12+, FastAPI, Celery + Redis, PostgreSQL + pgvector, OpenAI/Anthropic, Next.js.

---

## Quick start

**Requirements:** Python 3.12+, Docker (for Postgres/Redis), or local PostgreSQL 16 with [pgvector](https://github.com/pgvector/pgvector).

```bash
cd github-intel
cp .env.example .env   # set DATABASE_URL, REDIS_URL; optional: GITHUB_TOKEN, OPENAI_API_KEY
docker compose up -d postgres redis
pip install -e .
alembic upgrade head
python scripts/seed_categories.py
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

- **Health:** http://localhost:8000/api/v1/health  
- **API docs:** http://localhost:8000/docs  

To run the full pipeline (ingest → score → classify → content), start a Celery worker and trigger from the UI or API. See [LOCAL_SETUP.md](LOCAL_SETUP.md) for the complete local runbook and **how the pipeline works** (what each step does when you run it).

---

## Docker

| Goal | Command |
|------|--------|
| API only | `docker compose up -d postgres redis api` |
| API + worker (pipeline on-demand) | `docker compose up -d postgres redis api worker` |
| Full stack + frontend | `docker compose up -d postgres redis api worker frontend` |

**First-time setup in Docker:** run migrations and seed categories inside the API container:

```bash
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed_categories.py
```

**Trigger pipeline:** Use the dashboard “Run pipeline now” button, or:

```bash
curl -X POST http://localhost:8000/api/v1/pipeline/run
```

**Optional CLI ingestion:** `docker compose exec api python scripts/run_ingestion.py --trending` or `--search`.

---

## Running locally (no Docker for app)

**→ Full guide: [LOCAL_SETUP.md](LOCAL_SETUP.md)** — Postgres in Docker, API + worker + frontend on your machine, pipeline on-demand only.

Short version: start Postgres (and optionally Redis) with Docker, then run API, Celery worker, and frontend locally. Trigger the pipeline from the UI; results are stored in Postgres.

---

## Implementation phases

| Phase | Description |
|-------|-------------|
| 1 | Foundation ✅ |
| 2 | Ingestion pipeline ✅ |
| 3 | Scoring & quality filters ✅ |
| 4 | Classification (keyword + embedding + language) ✅ |
| 5 | Content generation (LLM) ✅ |
| 6 | API (trending, repos, categories, stats, pipeline) ✅ |
| 7 | Frontend (Next.js, dashboard, repo detail) ✅ |
| 8 | Integration & polish ✅ |

---

## Project layout

- `src/` — FastAPI app, models, services, LLM, API, Celery tasks
- `alembic/` — migrations
- `scripts/` — seed_categories, run_ingestion
- `frontend/` — Next.js app
- `tests/` — unit and integration

See `TechSpec-GitHub_Intelligence.md` for full structure.
