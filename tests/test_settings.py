"""api.settings — URL construction and defaults (issue #9). No database needed."""

import pytest


@pytest.fixture
def make_settings():
    from api.settings import Settings

    def _make(**overrides):
        # _env_file=None: never read a developer's .env in tests
        return Settings(_env_file=None, **overrides)

    return _make


def test_defaults(make_settings) -> None:
    s = make_settings()
    assert s.EMBEDDING_DIM == 384
    assert s.EMBEDDING_MODEL == "sentence-transformers/all-MiniLM-L6-v2"
    assert s.DEBUG is False
    assert s.API_KEY in (None, "")


def test_url_built_from_parts_when_database_url_unset(make_settings) -> None:
    s = make_settings(
        DATABASE_URL=None,
        POSTGRES_USER="u",
        POSTGRES_PASSWORD="p",
        POSTGRES_HOST="h",
        POSTGRES_PORT=5433,
        POSTGRES_DB="d",
    )
    assert s.sync_database_url == "postgresql+psycopg2://u:p@h:5433/d"
    assert s.async_database_url == "postgresql+asyncpg://u:p@h:5433/d"


@pytest.mark.parametrize(
    "given",
    [
        "postgresql://u:p@h:5432/d",
        "postgres://u:p@h:5432/d",  # Heroku/Railway style
        "postgresql+psycopg2://u:p@h:5432/d",  # already qualified: must not be double-mangled
        "postgresql+asyncpg://u:p@h:5432/d",
    ],
)
def test_driver_is_normalised_whatever_the_input_scheme(make_settings, given: str) -> None:
    s = make_settings(DATABASE_URL=given)
    assert s.sync_database_url == "postgresql+psycopg2://u:p@h:5432/d"
    assert s.async_database_url == "postgresql+asyncpg://u:p@h:5432/d"
