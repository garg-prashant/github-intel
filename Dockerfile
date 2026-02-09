FROM python:3.12-slim

WORKDIR /app

# Build deps for pgvector; then pip — this layer is cached when only code changes
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# App code last — changes here don't invalidate pip layer
COPY src/ src/
COPY alembic.ini .
COPY alembic/ alembic/

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
