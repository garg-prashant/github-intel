# Local setup (Postgres in Docker)

Run **only Postgres in Docker**. API, Celery worker, frontend, and Redis run on your machine. The pipeline is **on-demand only** — trigger from the UI or API; results are stored for the next run.

---

## Prerequisites

- **Python 3.12+**
- **Node.js 20+** (frontend)
- **Redis** — e.g. `brew install redis` then `brew services start redis` (macOS)
- **Docker** (for Postgres)

---

## 1. Postgres and env

```bash
cd github-intel
docker compose up -d postgres
```

Default DB: `localhost:5432`, user `github_intel`, password `github_intel_dev`, database `github_intel`. Ensure Redis is running locally.

```bash
cp .env.example .env
```

Set in `.env`:

- `DATABASE_URL=postgresql+asyncpg://github_intel:github_intel_dev@localhost:5432/github_intel`
- `REDIS_URL=redis://localhost:6379/0`
- Optional: `GITHUB_TOKEN`, `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` for ingestion and LLM

---

## 2. Backend

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
alembic upgrade head
python scripts/seed_categories.py
```

**Terminal 1 — API**

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Celery worker**

```bash
celery -A src.celery_app:celery worker --loglevel=info --queues=ingestion,scoring,classification,content
```

Optional: **Flower** (monitoring) — `pip install flower` then `celery -A src.celery_app:celery flower --port=5555` → http://localhost:5555

---

## 3. Frontend

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_URL=http://localhost:8000   # or .env.local
npm run dev
```

Open http://localhost:3000.

---

## 4. Getting data

The dashboard shows only repos with `quality_passed = true` (set by the scoring step). There is **no cron** — run the pipeline when you want new data.

- **UI:** Click **“Run pipeline now”** on the dashboard. Worker must be running; wait a few minutes and refresh.
- **API:** `curl -X POST http://localhost:8000/api/v1/pipeline/run`
- **CLI (ingestion only):** `python scripts/run_ingestion.py --trending` or `--search`, then trigger the rest from the UI.

#### How the pipeline works (what happens when you run it)

When you trigger the pipeline (UI or `POST /api/v1/pipeline/run`), a **Celery chain** runs **five steps in order**. Each step finishes before the next starts. The UI shows progress for each step.

| Step | What it does | Where data goes |
|------|--------------|-----------------|
| **1. Ingest trending** | Scrapes github.com/trending (daily/weekly, several languages). For each repo (capped by `MAX_TRENDING_REPOS`), calls GitHub API: repo metadata, README, languages, commit activity. | Inserts/updates `repositories` and `trend_snapshots`. Waits `GITHUB_REQUEST_DELAY_SECONDS` between repos to avoid rate limits. |
| **2. Ingest search** | For each of the 7 categories, runs a GitHub search query and takes up to `MAX_REPOS_PER_CATEGORY` repos. Fetches same metadata (repo, README, languages, commit activity) for each. | Same as above: `repositories` and `trend_snapshots`. De-duplicates by repo; total new/updated repos is at most ~35 (search) plus whatever came from trending. |
| **3. Score & filter** | Computes a trend score for every repo (from snapshots: stars/forks deltas, commit activity). Applies quality filters (e.g. min stars, not archived). Sets `quality_passed = true` for repos that pass. | Updates `repositories.current_trend_score` and `repositories.quality_passed`. |
| **4. Classify** | For repos that don’t yet have categories (or have fewer than 2), runs classification: **keyword** + **embedding** (README vs category profiles) + **language** signals. Combines into a confidence per category and assigns categories above a threshold. | Inserts/updates `repository_categories`. Embeddings are stored in `repo_embeddings` (local model by default, no OpenAI cost). |
| **5. Generate content** | Picks up to **top N repos per category** (N = `MAX_REPOS_PER_CATEGORY`) that have `quality_passed` and the fewest generated content rows. For each, generates up to 5 content types (quick start, mental model, recipe, etc.) via LLM, respecting `MAX_REPOS_PER_DAY`. | Inserts into `generated_content`. Uses OpenAI or Anthropic (set in `.env`); this is the step that incurs LLM cost. |

**Flow summary:** Ingest (GitHub → DB) → Score (DB) → Classify (DB + optional embeddings) → Content (LLM → DB). The dashboard and API read from `repositories`, `repository_categories`, and `generated_content`; only repos with `quality_passed = true` appear on the trending list.

Set `GITHUB_TOKEN` for better ingestion rate limits; set LLM keys for classification and content generation.

**Limiting repos (avoid GitHub rate limits and high OpenAI/Anthropic bills):**  
The app is configured to run on **top 5 repos per category** by default:

- **Search ingestion:** At most 5 repos per category (7 categories → up to 35 repos from search). Set `MAX_REPOS_PER_CATEGORY=5` in `.env` (default).
- **Trending ingestion:** Capped at 25 repos total across all trending views. Set `MAX_TRENDING_REPOS=25` in `.env` (default).
- **Content generation:** Only the top 5 repos per category (by trend score) get LLM-generated content; daily cap still applies via `MAX_REPOS_PER_DAY=20`.

So each pipeline run ingests at most ~35 (search) + 25 (trending) unique repos, and generates content for up to 5 per category (with a daily content cap).

**Avoiding GitHub 503 / rate limits:** Set `GITHUB_REQUEST_DELAY_SECONDS=1.0` (default) in `.env` so the worker waits 1 second between each repo during ingestion. That slows the run but prevents "503 Service Unavailable" and secondary rate limits. Increase to 1.5–2 if you still see 503s.

**Embeddings (no OpenAI cost):** Use local open-source embeddings so classification doesn’t call the OpenAI API. Set `EMBEDDING_PROVIDER=local` and `EMBEDDING_MODEL=all-MiniLM-L6-v2` in `.env` (defaults). Run `alembic upgrade head` so the `repo_embeddings` table uses 384-dim vectors. The first pipeline run will download the model (~80MB) once.

---

## 5. Sanity checks

```bash
curl -s http://localhost:8000/api/v1/health | jq
```

- API docs: http://localhost:8000/docs  
- Pipeline: `curl -X POST http://localhost:8000/api/v1/pipeline/run`  
- Ingestion only: `python scripts/run_ingestion.py --trending` or `--cleanup`

---

## Optional: Redis in Docker

```bash
docker compose up -d postgres redis
```

Use the same `.env`; API, worker, and frontend still run locally and connect to both containers.

---

## Summary

| Component   | Where it runs |
|------------|----------------|
| Postgres   | Docker |
| Redis      | Local (or Docker) |
| API        | Local |
| Celery worker | Local (on-demand pipeline) |
| Frontend   | Local (`npm run dev` in `frontend/`) |
