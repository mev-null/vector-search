"""api.embeddings (issue #7) and a sanity check of the test double."""

import math

import pytest

from tests.conftest import DIM, FakeEmbedder


def _norm(v: list[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def test_normalize_returns_unit_vector() -> None:
    from api.embeddings import normalize

    assert normalize([3.0, 4.0]) == pytest.approx([0.6, 0.8])
    assert normalize([0.0, 0.0]) == [0.0, 0.0], "zero vector must not divide by zero"


def test_fake_embedder_is_deterministic_and_normalised() -> None:
    e = FakeEmbedder()
    a1, a2, b = e.embed(["Spiral Galaxy", "spiral   galaxy", "aurora"])
    assert a1 == a2
    assert len(a1) == DIM
    assert _norm(a1) == pytest.approx(1.0)
    assert abs(_cos(a1, b)) < 0.5


@pytest.mark.slow
def test_real_model_matches_configured_dimension() -> None:
    """Downloads ~90 MB on first run. Guards against changing the model without a migration."""
    from api.embeddings import FastEmbedEmbedder
    from api.settings import settings

    e = FastEmbedEmbedder()
    (vec,) = e.embed(["Saturn's rings in infrared"])
    assert e.dim == settings.EMBEDDING_DIM == len(vec) == 384
    assert _norm(vec) == pytest.approx(1.0, abs=1e-3)
