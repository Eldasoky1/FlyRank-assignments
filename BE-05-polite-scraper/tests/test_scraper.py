"""Tests for the Polite Scraper.

Offline: they parse fixture HTML and exercise politeness/validation logic
without touching the live site (which is slow and should not be hammered
by a test-suite). Run:

    pip install -r requirements.txt
    pytest tests/ -q
"""

from pathlib import Path

import pytest

from models import Book
from scraper import PoliteScraper

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def scraper():
    s = PoliteScraper(delay=0.0, retries=1, backoff=0.0)
    return s


def _detail_soup():
    from bs4 import BeautifulSoup

    return BeautifulSoup((FIXTURES / "book-detail.html").read_text(encoding="utf-8"), "html.parser")


def _catalogue_soup():
    from bs4 import BeautifulSoup

    return BeautifulSoup((FIXTURES / "catalogue.html").read_text(encoding="utf-8"), "html.parser")


# ---- schema coercion (the "messy text -> typed values" requirement) ----


def test_price_currency_to_float():
    assert Book._parse_price("£51.77") == 51.77
    assert Book._parse_price("£1,234.56") == 1234.56


def test_rating_word_to_int():
    assert Book._parse_rating("Three") == 3
    assert Book._parse_rating("five") == 5
    assert Book._parse_rating("one") == 1


def test_availability_to_count_and_bool():
    assert Book._parse_availability_count("In stock (19 available)") == 19
    assert Book._parse_availability_count("Out of stock") == 0
    assert Book._parse_in_stock("In stock (19 available)") is True
    assert Book._parse_in_stock("Out of stock") is False


# ---- parsing a real fixture page ----


def test_parse_book_fully(scraper):
    book = scraper.scrape_book("https://books.toscrape.com/catalogue/a-light_1000/", _detail_soup())
    assert book is not None
    assert book.model_dump()["title"] == "A Light in the Attic"
    assert book.price_gbp == 51.77
    assert book.rating == 3
    assert book.in_stock is True
    assert book.availability_count == 19
    assert book.category == "Poetry"
    assert "poetry" in book.description.lower()
    assert book.upc == "a897fe39b1053632"


# ---- validation drops invalid records gracefully ----


def test_invalid_record_is_rejected_not_crash():
    with pytest.raises(Exception):
        Book(title="", upc="", price_gbp=0, price_excl_tax_gbp=0, price_incl_tax_gbp=0,
             tax_gbp=0, rating=0, in_stock=False, availability_text="", availability_count=0,
             number_of_reviews=0)


# ---- robots.txt politeness ----


def test_robots_disallow_parsing():
    robots = (
        "User-agent: *\n"
        "Disallow: /catalogue/\n"
        "Disallow: /assets/\n"
        "Allow: /$\n"
    )
    disallowed = PoliteScraper._parse_disallow(robots)
    assert "/catalogue/" in disallowed
    assert "/assets/" in disallowed


def test_is_allowed_after_parse(scraper):
    scraper.disallowed_prefixes = ["/catalogue/"]
    assert scraper.is_allowed("https://books.toscrape.com/") is True
    assert scraper.is_allowed("https://books.toscrape.com/catalogue/x.html") is False


# ---- error handling / missing pages ----


def test_missing_page_returns_none_no_crash(monkeypatch, scraper):
    class _Resp:
        status_code = 404
        raise_for_status = lambda self: (_ for _ in ()).throw(Exception("404"))
    monkeypatch.setattr(scraper.session, "get", lambda *a, **k: _Resp())
    out = scraper.get("https://books.toscrape.com/missing.html")
    assert out is None  # gracefully handled


def test_request_exception_returns_none_no_crash(monkeypatch, scraper):
    def boom(*a, **k):
        raise __import__("requests").RequestException("boom")
    monkeypatch.setattr(scraper.session, "get", boom)
    assert scraper.get("https://books.toscrape.com/") is None


# ---- catalogue page linking ----


def test_catalogue_page_extracts_three_urls(scraper):
    base = "https://books.toscrape.com/catalogue/page-1.html"
    urls = scraper._parse_urls(_catalogue_soup(), base)
    assert len(urls) == 3
    assert all(url.startswith("https://books.toscrape.com/catalogue/") for url in urls)


# ---- throttle / politeness timer ----


def test_throttle_enforces_delay():
    import time

    s = PoliteScraper(delay=0.2, retries=1, backoff=0.0)
    s._throttle()
    start = time.monotonic()
    s._throttle()
    assert time.monotonic() - start >= 0.2
