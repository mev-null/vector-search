"""Shared fixtures for the contract test suite.

The suite runs against a real PostgreSQL with the pgvector extension:

* CI: the ``pgvector/pgvector:pg16`` service container (see .github/workflows/ci.yml).
* Locally: ``docker compose up -d db`` and, if needed,
  ``TEST_DATABASE_URL=postgresql://apod:apod@localhost:5432/apod_test uv run pytest``.
  The database named in the URL is created on first run if it does not exist.

The embedding model is never loaded here. ``api.embeddings.get_embedder`` is overridden with a
deterministic offline fake, so the tests exercise ordering, idempotency and dimension handling
without a model download. The single test that loads the real model is marked ``slow``.

Environment variables are set *before* ``api.*`` is imported because settings are read at
import time; every ``api`` import below therefore happens inside fixtures.
"""

from __future__ import annotations

import hashlib
import math
import os
import subprocess
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent.parent
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://apod:apod@localhost:5432/apod_test")
DIM = 384

os.environ["DATABASE_URL"] = TEST_DB_URL
os.environ.setdefault("API_KEY", "")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("EMBEDDING_DIM", str(DIM))


class FakeEmbedder:
    """Deterministic stand-in for the real model.

    Identical texts (modulo case/whitespace) map to identical unit vectors; different texts map
    to pseudo-random unit vectors whose cosine similarity is ~0. That is exactly what the search
    tests need: an exact-text query must come back first with score ~1, everything else far below.
    """

    dim = DIM

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    @staticmethod
    def _one(text_: str) -> list[float]:
        seed = hashlib.sha256(" ".join(text_.lower().split()).encode()).digest()
        vals: list[float] = []
        counter = 0
        while len(vals) < DIM:
            block = hashlib.sha256(seed + counter.to_bytes(2, "big")).digest()
            vals.extend((b / 127.5) - 1.0 for b in block)
            counter += 1
        vals = vals[:DIM]
        norm = math.sqrt(sum(v * v for v in vals)) or 1.0
        return [v / norm for v in vals]


def _ensure_database_exists(url: str) -> None:
    """Create the test database if it is missing (connects to the maintenance DB)."""
    import psycopg2
    from psycopg2 import sql

    parts = urlsplit(url)
    dbname = parts.path.lstrip("/")
    admin_url = urlunsplit(parts._replace(path="/postgres"))
    conn = psycopg2.connect(admin_url)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    finally:
        conn.close()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    """Apply alembic migrations once per session against TEST_DATABASE_URL."""
    _ensure_database_exists(TEST_DB_URL)
    env = {**os.environ, "DATABASE_URL": TEST_DB_URL}
    subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ROOT / "api" / "alembic.ini"),
            "upgrade",
            "head",
        ],
        check=True,
        cwd=ROOT,
        env=env,
    )
    yield


@pytest.fixture(autouse=True)
async def clean_tables() -> AsyncIterator[None]:
    """Start every test from an empty table; dispose the engine so no connection outlives the loop."""
    from api.database import engine

    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE apod"))
    yield
    await engine.dispose()


@pytest.fixture
def fake_embedder() -> FakeEmbedder:
    return FakeEmbedder()


@pytest.fixture
async def client(fake_embedder: FakeEmbedder) -> AsyncIterator[AsyncClient]:
    """ASGI client with the embedding dependency stubbed. Lifespan is intentionally not run."""
    from api.embeddings import get_embedder
    from api.main import app

    app.dependency_overrides[get_embedder] = lambda: fake_embedder
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def apod(date: str, title: str, explanation: str | None = None) -> dict[str, str]:
    """Build a valid POST /data item."""
    return {
        "title": title,
        "explanation": explanation or f"{title} — description",
        "url": f"https://apod.nasa.gov/apod/image/{date.replace('-', '')}.jpg",
        "date": date,
    }
