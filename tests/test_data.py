"""POST/GET/DELETE /data — ingest contract (issues #8, #9, #10)."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.conftest import apod

EXPECTED_KEYS = {"id", "title", "explanation", "url", "date"}


async def test_post_creates_rows(client: AsyncClient) -> None:
    r = await client.post("/data", json=[apod("2025-01-01", "Aurora"), apod("2025-01-02", "Comet")])
    assert r.status_code == 201, r.text
    body = r.json()
    assert len(body) == 2
    assert set(body[0]) == EXPECTED_KEYS
    assert {row["date"] for row in body} == {"2025-01-01", "2025-01-02"}


@pytest.mark.parametrize(
    "item",
    [
        {"title": "only a title"},
        {**apod("2025-01-01", "x"), "date": "2025-13-40"},
        {**apod("2025-01-01", "x"), "explanation": None},
        {**apod("2025-01-01", "x"), "url": ""},
    ],
    ids=["missing-fields", "bad-date", "null-explanation", "empty-url"],
)
async def test_post_invalid_input_is_422_not_500(client: AsyncClient, item: dict) -> None:
    r = await client.post("/data", json=[item])
    assert r.status_code == 422, r.text


async def test_upsert_on_date_is_idempotent(client: AsyncClient) -> None:
    first = await client.post("/data", json=[apod("2025-02-01", "Old title")])
    second = await client.post("/data", json=[apod("2025-02-01", "New title")])
    assert first.status_code == second.status_code == 201

    listing = await client.get("/data")
    rows = listing.json()
    assert len(rows) == 1, "re-posting the same date must update, not duplicate"
    assert rows[0]["title"] == "New title"
    assert rows[0]["id"] == first.json()[0]["id"], "upsert keeps the original id"


async def test_post_is_atomic(client: AsyncClient) -> None:
    """One bad item fails the whole batch — no partial ingest."""
    r = await client.post(
        "/data", json=[apod("2025-03-01", "good"), {"title": "bad item, missing the rest"}]
    )
    assert r.status_code == 422
    assert (await client.get("/data")).json() == []


async def test_list_is_paginated_newest_first(client: AsyncClient) -> None:
    await client.post(
        "/data",
        json=[apod("2025-04-01", "a"), apod("2025-04-03", "c"), apod("2025-04-02", "b")],
    )
    page1 = (await client.get("/data", params={"limit": 2})).json()
    page2 = (await client.get("/data", params={"limit": 2, "offset": 2})).json()
    assert [r["date"] for r in page1] == ["2025-04-03", "2025-04-02"]
    assert [r["date"] for r in page2] == ["2025-04-01"]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
async def test_list_validates_pagination(client: AsyncClient, params: dict) -> None:
    assert (await client.get("/data", params=params)).status_code == 422


async def test_get_by_id(client: AsyncClient) -> None:
    created = (await client.post("/data", json=[apod("2025-05-01", "Nebula")])).json()[0]
    r = await client.get(f"/data/{created['id']}")
    assert r.status_code == 200
    assert r.json() == created
    assert (await client.get(f"/data/{uuid4()}")).status_code == 404
    assert (await client.get("/data/not-a-uuid")).status_code == 422


async def test_delete_by_id(client: AsyncClient) -> None:
    created = (await client.post("/data", json=[apod("2025-06-01", "Eclipse")])).json()[0]
    assert (await client.delete(f"/data/{created['id']}")).status_code == 204
    assert (await client.delete(f"/data/{created['id']}")).status_code == 404
    assert (await client.get(f"/data/{created['id']}")).status_code == 404


async def test_write_endpoints_require_api_key_when_configured(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from api.settings import settings

    monkeypatch.setattr(settings, "API_KEY", "s3cret")

    assert (await client.post("/data", json=[apod("2025-07-01", "x")])).status_code == 401
    ok = await client.post("/data", json=[apod("2025-07-01", "x")], headers={"X-API-Key": "s3cret"})
    assert ok.status_code == 201
    row_id = ok.json()[0]["id"]
    assert (await client.delete(f"/data/{row_id}")).status_code == 401
    assert (
        await client.delete(f"/data/{row_id}", headers={"X-API-Key": "s3cret"})
    ).status_code == 204
    # reads stay open
    assert (await client.get("/data")).status_code == 200
