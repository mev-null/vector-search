"""POST /search — ranking contract (issues #8, #10).

Documents are embedded from their ``explanation``; with the deterministic FakeEmbedder an exact
text match has cosine distance 0 (score 1.0) and unrelated texts sit near 0.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import apod

DOCS = [
    apod("2025-01-01", "Galaxy", "A spiral galaxy seen face-on with bright blue arms"),
    apod("2025-01-02", "Aurora", "Green aurora curtains over a frozen lake in Iceland"),
    apod("2025-01-03", "Saturn", "Saturn's rings photographed in infrared by Cassini"),
]
RESULT_KEYS = {"id", "title", "explanation", "url", "date", "score"}


@pytest.fixture
async def seeded(client: AsyncClient) -> AsyncClient:
    r = await client.post("/data", json=DOCS)
    assert r.status_code == 201, r.text
    return client


async def test_exact_match_ranks_first_with_score_one(seeded: AsyncClient) -> None:
    r = await seeded.post("/search", json={"query": DOCS[1]["explanation"]})
    assert r.status_code == 200, r.text
    results = r.json()
    assert len(results) == 3
    assert set(results[0]) == RESULT_KEYS
    assert results[0]["title"] == "Aurora"
    assert results[0]["score"] == pytest.approx(1.0, abs=1e-4)
    assert all(res["score"] < 0.5 for res in results[1:])
    scores = [res["score"] for res in results]
    assert scores == sorted(scores, reverse=True), "results are ordered by similarity"


async def test_limit_is_respected(seeded: AsyncClient) -> None:
    r = await seeded.post("/search", json={"query": "galaxy", "limit": 1})
    assert r.status_code == 200
    assert len(r.json()) == 1


async def test_default_limit_is_ten(client: AsyncClient) -> None:
    docs = [apod(f"2025-02-{d:02d}", f"doc {d}") for d in range(1, 13)]
    assert (await client.post("/data", json=docs)).status_code == 201
    r = await client.post("/search", json={"query": "anything"})
    assert len(r.json()) == 10


@pytest.mark.parametrize(
    "body",
    [{"query": "x", "limit": 0}, {"query": "x", "limit": 101}, {"query": ""}, {"limit": 5}],
    ids=["limit-0", "limit-101", "empty-query", "missing-query"],
)
async def test_invalid_search_is_422(client: AsyncClient, body: dict) -> None:
    assert (await client.post("/search", json=body)).status_code == 422


async def test_search_on_empty_table_returns_empty_list(client: AsyncClient) -> None:
    r = await client.post("/search", json={"query": "spiral galaxy"})
    assert r.status_code == 200
    assert r.json() == []
