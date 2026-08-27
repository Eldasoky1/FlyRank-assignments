"""BE-08 · tests for the PDF report generator.

All offline — no network. Verifies data loading, statistics, the real PDF
output (magic bytes, %PDF header, %%EOF trailer, non-trivial size), and the
FastAPI endpoint contract.

Run:
    pip install -r requirements.txt
    pytest tests/ -q
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from report import (
    DEFAULT_DATA,
    average_price_by_category,
    compute_stats,
    generate_report,
    load_books,
    rating_distribution,
    render_pdf_bytes,
)
import app as app_module


@pytest.fixture(scope="module")
def books():
    return load_books(DEFAULT_DATA)


@pytest.fixture(scope="module")
def client():
    return TestClient(app_module.app)


def _is_pdf(b: bytes) -> bool:
    return b.startswith(b"%PDF") and b.rstrip().endswith(b"%%EOF") and len(b) > 1000


# ---- data loading ----


def test_load_books_returns_good_sample(books):
    assert isinstance(books, list)
    assert len(books) == 60


def test_load_books_has_expected_fields(books):
    for b in books:
        assert b["title"]
        assert b["category"]
        assert float(b["price_gbp"]) >= 0
        assert 1 <= int(b["rating"]) <= 5


def test_load_books_raises_on_bad_shape(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"books": "not a list"}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_books(bad)


# ---- statistics ----


def test_compute_stats_count(books):
    s = compute_stats(books)
    assert s["count"] == 60
    assert s["total_value_gbp"] > 0
    assert s["avg_price_gbp"] > 0


def test_compute_stats_empty_no_div_zero():
    s = compute_stats([])
    assert s["count"] == 0
    assert s["avg_price_gbp"] == 0.0


def test_avg_price_by_category_covers_all_and_is_sane(books):
    avg = average_price_by_category(books)
    assert len(avg) >= 1
    for v in avg.values():
        assert isinstance(v, float)
        assert v >= 0


def test_rating_distribution_sums_to_count(books):
    dist = rating_distribution(books)
    assert sum(dist.values()) == len(books)
    assert set(dist.keys()) <= {1, 2, 3, 4, 5}


# ---- PDF generation ----


def test_generate_report_writes_valid_pdf(tmp_path, books):
    out = tmp_path / "report.pdf"
    path = generate_report(books, out_path=out)
    raw = path.read_bytes()
    assert path.exists()
    assert _is_pdf(raw)
    assert raw.startswith(b"%PDF")


def test_render_pdf_bytes_valid(books):
    raw = render_pdf_bytes(books)
    assert _is_pdf(raw)
    assert b"Average price by category" in raw or b"Books" in raw


def test_render_allows_custom_title(books):
    raw = render_pdf_bytes(books, title="Quarterly Books Report")
    assert len(raw) > 1000
    assert raw.startswith(b"%PDF")


# ---- HTTP API ----


def test_stats_endpoint(client):
    r = client.get("/stats")
    assert r.status_code == 200
    assert r.json()["count"] == 60


def test_report_endpoint_returns_pdf(client):
    r = client.get("/report")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/pdf")
    assert _is_pdf(r.content)


def test_root_endpoint_lists_routes(client):
    r = client.get("/")
    assert r.json()["name"] == "PDF Report Generator API"
    assert r.json()["report"] == "/report"
