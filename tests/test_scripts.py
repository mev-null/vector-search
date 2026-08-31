"""api.scripts.load_data — pure helpers only; no network (issue #12)."""

from datetime import date

import pytest


@pytest.fixture
def mod():
    from api.scripts import load_data

    return load_data


def test_parse_args_days_default(mod) -> None:
    ns = mod.parse_args([])
    assert ns.days == 30
    assert ns.api_url == "http://127.0.0.1:8000"
    assert ns.batch_size == 50


def test_parse_args_explicit_range(mod) -> None:
    ns = mod.parse_args(["--start", "2025-01-01", "--end", "2025-01-31", "--api-url", "http://x:1"])
    assert (ns.start, ns.end) == (date(2025, 1, 1), date(2025, 1, 31))
    assert ns.api_url == "http://x:1"


def test_parse_args_rejects_days_with_range(mod) -> None:
    with pytest.raises(SystemExit):
        mod.parse_args(["--days", "5", "--start", "2025-01-01", "--end", "2025-01-02"])


def test_request_params_use_a_single_range_query(mod) -> None:
    params = mod.build_request_params(date(2025, 1, 1), date(2025, 1, 31), api_key="KEY")
    assert params == {"api_key": "KEY", "start_date": "2025-01-01", "end_date": "2025-01-31"}


def test_keep_images_filters_and_projects(mod) -> None:
    raw = [
        {
            "date": "2025-01-01",
            "title": "A",
            "explanation": "e",
            "url": "u",
            "hdurl": "h",
            "media_type": "image",
        },
        {"date": "2025-01-02", "title": "V", "explanation": "e", "url": "u", "media_type": "video"},
        {"date": "2025-01-03", "title": "no explanation", "url": "u", "media_type": "image"},
    ]
    kept = mod.keep_images(raw)
    assert kept == [{"date": "2025-01-01", "title": "A", "explanation": "e", "url": "u"}]


def test_batched(mod) -> None:
    assert list(mod.batched([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
