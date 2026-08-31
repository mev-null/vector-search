"""GET /health and GET / (issue #10)."""

from httpx import AsyncClient


async def test_health_reports_db_ok(client: AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "db": "ok"}


async def test_root_points_to_docs(client: AsyncClient) -> None:
    r = await client.get("/")
    assert r.status_code == 200
    assert "/docs" in r.text
