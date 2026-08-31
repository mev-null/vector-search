# NASA APOD Semantic Search

[![CI](https://github.com/mev-null/vector-search/actions/workflows/ci.yml/badge.svg)](https://github.com/mev-null/vector-search/actions/workflows/ci.yml)
![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Search NASA's [Astronomy Picture of the Day](https://apod.nasa.gov/apod/astropix.html) archive
in plain language — *"a spiral galaxy seen face-on"*, *"aurora over a frozen lake"* — and get
the pictures whose descriptions mean that, not just the ones that contain those words.

FastAPI · SQLModel · PostgreSQL + pgvector (HNSW, cosine) · fastembed (ONNX, no GPU, no API key) · Alembic · Docker Compose

> **Status:** the service is being brought back to a green build — see the
> [tracking issue](https://github.com/mev-null/vector-search/issues/13). This README describes
> the target behaviour; `tests/` is the executable version of it.

```bash
curl -s localhost:8000/search \
  -H 'content-type: application/json' \
  -d '{"query": "a spiral galaxy seen face-on", "limit": 3}' | jq
```
```json
[
  {
    "id": "0192a9c4-3e6b-7d1a-9f1e-2b0c8e5a7d21",
    "title": "NGC 1232: A Grand Design Spiral Galaxy",
    "explanation": "Galaxies are fascinating not only for what is visible, but for what is invisible ...",
    "url": "https://apod.nasa.gov/apod/image/2501/NGC1232_VLT_960.jpg",
    "date": "2025-01-14",
    "score": 0.71
  }
]
```

## How it works

```mermaid
flowchart LR
    subgraph ingest["Ingest (api/scripts/load_data.py)"]
        NASA["NASA APOD API<br/>start_date … end_date"] -->|images only| POST["POST /data"]
    end
    subgraph api["FastAPI (api/)"]
        POST --> EMB["fastembed<br/>all-MiniLM-L6-v2 · 384-d · L2-normalised"]
        Q["POST /search {query, limit}"] --> EMB
        EMB -->|upsert on date| PG[("PostgreSQL 16 + pgvector<br/>apod(embedding vector(384))<br/>HNSW · vector_cosine_ops")]
        EMB -->|"ORDER BY embedding <=> q LIMIT n"| PG
        PG --> RES["[{title, url, date, explanation, score}]"]
    end
```

1. **Ingest** — one request to the APOD API for a date range, keep `media_type == "image"`, embed
   each `explanation`, and upsert on `date` (APOD publishes one picture per day, so `date` is the
   natural key; re-running the loader never duplicates).
2. **Query** — embed the query with the *same* model instance (one `Embedder` dependency for both
   paths, so read and write can never drift), then `ORDER BY embedding <=> :q` — cosine distance
   served by an HNSW index. `score = 1 − distance`.
3. **Schema** — SQLModel models, Alembic migrations, `CREATE EXTENSION vector` in the baseline.
   Migrations run automatically when the container starts.

## Quick start

Requirements: Docker with the compose plugin. No GPU, no API key for searching.

```bash
cp .env.example .env                 # defaults work out of the box
docker compose up -d --build         # db (pgvector) + app; migrations run on boot
curl -s localhost:8000/health        # {"status":"ok","db":"ok"}

# Load the last 30 days of pictures (DEMO_KEY is fine for this — it is one request)
docker compose exec app python -m api.scripts.load_data --days 30

open http://localhost:8000/docs      # interactive API docs (Swagger UI)
```

A free [NASA API key](https://api.nasa.gov/) lifts the `DEMO_KEY` limit (30 req/h) if you want
to backfill years of pictures: set `NASA_API_KEY` in `.env` and pass `--start 2015-01-01`.

## API

| Method | Path | Body / params | Returns |
|---|---|---|---|
| `GET` | `/health` | – | `{"status":"ok","db":"ok"}`, `503` if the DB is unreachable |
| `POST` | `/search` | `{"query": str, "limit": 1‑100 = 10}` | results ordered by similarity, each with `score` |
| `POST` | `/data` | `[{title, explanation, url, date}]` | `201` created/updated rows — **upsert on `date`**, one transaction |
| `GET` | `/data` | `?limit=1‑100&offset=0` | rows, newest `date` first |
| `GET` | `/data/{id}` | – | one row or `404` |
| `DELETE` | `/data/{id}` | – | `204` or `404` |

Write endpoints (`POST /data`, `DELETE /data/{id}`) require the header `X-API-Key` when `API_KEY`
is set in the environment; leave it empty for local use. Invalid input is a `422` with field
errors, never a `500`.

## Development

```bash
uv sync --group dev                  # Python 3.12+, uv
docker compose up -d db              # a pgvector Postgres for the tests
uv run pytest -m "not slow"          # contract suite (creates the apod_test database on first run)
uv run pytest -m slow                # one test that downloads the real model (~90 MB) and checks 384-d
uv run ruff format && uv run ruff check
uv run alembic -c api/alembic.ini revision --autogenerate -m "describe change"
```

Tests talk to a real PostgreSQL (`TEST_DATABASE_URL`, default
`postgresql://apod:apod@localhost:5432/apod_test`) but never load the embedding model: the
`get_embedder` dependency is swapped for a deterministic fake, so the suite is fast and offline.
CI runs the same steps against a `pgvector/pgvector:pg16` service container and also builds the
Docker image.

```
.
├── api/
│   ├── main.py            FastAPI app, lifespan (model warm-up + dimension check), routers
│   ├── settings.py        pydantic-settings: DB URLs, NASA_API_KEY, API_KEY, EMBEDDING_*
│   ├── database.py        async engine + session dependency (asyncpg)
│   ├── embeddings.py      Embedder protocol, fastembed implementation, get_embedder()
│   ├── models.py          SQLModel: Apod (date unique, embedding vector(384), timestamptz)
│   ├── schemas.py         request/response models (Pydantic v2)
│   ├── crud.py            upsert_many, search (cosine distance), get/list/delete
│   ├── routers/           search.py, data.py, ops.py (health)
│   ├── migrations/        Alembic (baseline creates the extension, table and HNSW index)
│   └── scripts/load_data.py   APOD → POST /data, range query, batching, retries
├── tests/                 contract suite (httpx ASGI client, real Postgres, fake embedder)
├── docker-compose.yml     db (pgvector) + app; app runs `alembic upgrade head` on boot
├── Dockerfile             python:3.12-slim + uv, non-root
└── .env.example           every variable, with defaults that work
```

## Design notes

- **Why fastembed** — the original build used `sentence-transformers` (PyTorch, >1 GB image);
  fastembed runs the same `all-MiniLM-L6-v2` weights on ONNX Runtime in ~90 MB with no API key,
  which keeps "anyone can `docker compose up`" true. The dimension (384) is asserted at start-up
  against the DB column so the model cannot be swapped without a migration.
- **Cosine + HNSW** — embeddings are L2-normalised on write, the query uses `<=>`
  (`cosine_distance`) and the index is built with `vector_cosine_ops`; operator and opclass must
  match or Postgres falls back to a sequential scan.
- **Upsert on `date`** — ingest is idempotent and atomic (one transaction per batch), so a
  half-failed load never leaves partial rows.
- **Migrations on boot** — the container entrypoint runs `alembic upgrade head` before uvicorn;
  CI runs `alembic check` so the models and the migrations cannot drift.

## License

MIT — see [LICENSE](LICENSE). Images and text returned by the API belong to their respective
owners and are served from NASA APOD; see [APOD image permissions](https://apod.nasa.gov/apod/lib/about_apod.html#srapply).
