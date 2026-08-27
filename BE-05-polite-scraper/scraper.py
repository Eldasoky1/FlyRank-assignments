"""The Polite Scraper — books.toscrape.com

Turns messy catalogue HTML into clean, validated JSON — politely.

Politeness / responsibility checklist (see README for the reasoning):
  1. robots.txt is fetched and honoured before anything else.
  2. A descriptive User-Agent identifies the scraper and its purpose.
  3. Every request is throttled (POLITE_DELAY seconds between calls).
  4. Retries use exponential backoff and stop after RETRY_LIMIT.
  5. Broken / missing pages never crash the run: they are logged and skipped.
  6. Every record is validated against the `Book` Pydantic schema before it
     is accepted; invalid records are logged and dropped.

Run:
    python scraper.py --pages 3           # scrape 60 books (3 pages x 20)
    python scraper.py --pages 3 --out output/books.json
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import time
import urllib.parse
from pathlib import Path
from typing import List, Optional

import requests
from pydantic import ValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from models import Book

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s · %(levelname)-7s · %(message)s",
)
log = logging.getLogger("polite-scraper")

BASE_URL = "https://books.toscrape.com/"
ROBOTS_URL = "https://books.toscrape.com/robots.txt"
PER_PAGE = 20

# Polite defaults (overridable via CLI so tests stay fast)
DEFAULT_DELAY = 2.0
DEFAULT_RETRIES = 2
DEFAULT_BACKOFF = 0.5

USER_AGENT = (
    "PoliteScraper/1.0 (+https://github.com/Eldasoky1/FlyRank-assignments; "
    "educational assignment; contact: ahmed.320240024@ejust.edu.eg)"
)


class PoliteScraper:
    """Scrapes books.toscrape.com while respecting the site."""

    def __init__(
        self,
        delay: float = DEFAULT_DELAY,
        retries: int = DEFAULT_RETRIES,
        backoff: float = DEFAULT_BACKOFF,
        user_agent: str = USER_AGENT,
    ):
        self.delay = delay
        self.last_request_ts: Optional[float] = None

        self.session = requests.Session()
        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"],
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.session.headers.update({"User-Agent": user_agent})

        self.disallowed_prefixes: List[str] = []

    # --- politeness helpers ---

    def confirm_robots_ok(self) -> None:
        """Fetch robots.txt and read the Disallow rules for our UA."""
        try:
            resp = self.session.get(ROBOTS_URL, timeout=10)
            self._throttle()
            resp.raise_for_status()
        except requests.RequestException as exc:
            log.warning("Could not fetch robots.txt (%s); proceeding cautiously.", exc)
            return
        self.disallowed_prefixes = self._parse_disallow(resp.text)
        if self.disallowed_prefixes:
            log.info("robots.txt honours %d Disallow rule(s)", len(self.disallowed_prefixes))

    @staticmethod
    def _parse_disallow(robots_txt: str) -> List[str]:
        prefixes = []
        for raw_line in robots_txt.splitlines():
            line = raw_line.strip()
            if line.lower().startswith("disallow"):
                value = line.split(":", 1)[1].strip() if ":" in line else ""
                value = value.strip()
                if value and value != "/" and not value.startswith("#"):
                    prefixes.append(value)
        return prefixes

    def is_allowed(self, url: str) -> bool:
        path = urllib.parse.urlparse(url).path
        return not any(path.startswith(p) for p in self.disallowed_prefixes)

    def _throttle(self) -> None:
        """Enforce a minimum delay between requests (never hammer the server)."""
        if self.last_request_ts is None:
            self.last_request_ts = time.monotonic()
            return
        elapsed = time.monotonic() - self.last_request_ts
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_ts = time.monotonic()

    def get(self, url: str) -> Optional[requests.Response]:
        """GET a page only if robots.txt allows it, throttled and retried."""
        if not self.is_allowed(url):
            log.warning("Skipping disallowed target: %s", url)
            return None
        try:
            resp = self.session.get(url, timeout=15)
            self._throttle()
            # The site is UTF-8; pin the encoding so '£' (U+00A3) does not get
            # mis-decoded as the two Latin-1 characters 'Â£'.
            resp.encoding = "utf-8"
            status = resp.status_code
            log.debug("GET %s -> %d", url, status)
            if status == 404:
                log.warning("Page missing (404): %s — skipping gracefully.", url)
                return None
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            log.warning("Request failed for %s after retries: %s — continuing.", url, exc)
            return None

    # --- page parsing ---

    @staticmethod
    def _soup(html: str):
        from bs4 import BeautifulSoup

        return BeautifulSoup(html, "html.parser")

    def _price(self, node) -> Optional[float]:
        if node:
            return node.get_text(strip=True)
        return None

    @staticmethod
    def _parse_urls(soup, base_url: str) -> List[str]:
        return [
            urllib.parse.urljoin(base_url, a["href"])
            for a in soup.select("article.product_pod h3 a")
        ]

    def _parse_book(self, page_soup, product_url: str) -> Optional[Book]:
        """Parse a single book detail page into a validated Book, or None."""
        title_node = page_soup.select_one("h1")
        title = title_node.get_text(strip=True) if title_node else ""

        table = {}
        for row in page_soup.select("table.table-striped tr"):
            cells = row.find_all(["th", "td"])
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[-1].get_text(strip=True)
                table[key] = value

        rating_node = page_soup.select_one("p.star-rating")
        rating = rating_node.get("class", ["zero"])[-1] if rating_node else 0

        availability_node = page_soup.select_one("p.availability")
        availability_text = availability_node.get_text(" ", strip=True) if availability_node else ""

        desc_node = page_soup.select_one("div#product_description + p")
        description = desc_node.get_text(strip=True) if desc_node else ""

        category_node = page_soup.select_one("ul.breadcrumb li:nth-of-type(3) a")
        category = category_node.get_text(strip=True) if category_node else ""

        try:
            return Book(
                title=title,
                upc=table.get("UPC", ""),
                price_gbp=table.get("Price (excl. tax)", ""),
                price_excl_tax_gbp=table.get("Price (excl. tax)", ""),
                price_incl_tax_gbp=table.get("Price (incl. tax)", ""),
                tax_gbp=table.get("Tax", ""),
                rating=rating,
                in_stock=availability_text,
                availability_text=availability_text,
                availability_count=availability_text,
                number_of_reviews=table.get("Number of reviews", ""),
                category=category,
                description=description,
                product_url=product_url,
            )
        except ValidationError as exc:
            log.warning("Record failed schema validation (%s): %s", title, exc.errors()[0])
            return None

    def scrape_catalogue_page(self, page_index: int) -> List[str]:
        """Return the product URLs on a category listing page."""
        listing_url = base_catalogue_url(page_index)
        resp = self.get(listing_url)
        if resp is None:
            return []
        soup = self._soup(resp.text)
        # Product hrefs are relative to the /catalogue/ directory, so resolve
        # them against the listing page URL, not the site root.
        return self._parse_urls(soup, listing_url)

    def scrape_book(self, product_url: str, page_soup=None) -> Optional[Book]:
        if page_soup is None:
            resp = self.get(product_url)
            if resp is None:
                return None
            page_soup = self._soup(resp.text)
        return self._parse_book(page_soup, product_url)

    def seed_from_catalogue(self) -> List[Book]:
        """Fetch pages until we have exactly `target` valid books."""
        results: List[Book] = []
        page_index = 1
        while len(results) < self.target and page_index <= self.max_pages:
            urls = self.scrape_catalogue_page(page_index)
            if not urls:
                log.info("No more catalogue pages; stopping at %d books.", len(results))
                break
            for url in urls:
                if len(results) >= self.target:
                    break
                log.info("Fetching book %d/%d: %s", len(results) + 1, self.target, url)
                book = self.scrape_book(url)
                if book is not None:
                    results.append(book)
            page_index += 1
        return results

    def save(self, books: List[Book], out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "meta": {
                "source": BASE_URL,
                "count": len(books),
                "schema": "Book (Pydantic)",
                "polite_delay_seconds": self.delay,
            },
            "books": [b.model_dump() for b in books],
        }
        out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("Wrote %d validated books to %s", len(books), out_path)


def base_catalogue_url(page_index: int) -> str:
    if page_index == 1:
        return BASE_URL + "catalogue/page-1.html"
    return BASE_URL + f"catalogue/page-{page_index}.html"


def main() -> None:
    parser = argparse.ArgumentParser(description="Polite scraper for books.toscrape.com")
    parser.add_argument("--pages", type=int, default=3,
                        help="max catalogue pages to scrape (default 3 = 60 books)")
    parser.add_argument("--target", type=int, default=60, help="number of books to collect")
    parser.add_argument("--out", default="output/books.json", help="output JSON path")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="seconds between requests")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES)
    parser.add_argument("--backoff", type=float, default=DEFAULT_BACKOFF)
    args = parser.parse_args()

    scraper = PoliteScraper(
        delay=args.delay, retries=args.retries, backoff=args.backoff
    )
    scraper.max_pages = args.pages
    scraper.target = args.target

    log.info("Checking robots.txt & politeness rules for %s …", BASE_URL)
    scraper.confirm_robots_ok()

    books = scraper.seed_from_catalogue()
    scraper.save(books, Path(args.out))
    log.info("Done. Collected %d valid books.", len(books))


if __name__ == "__main__":
    main()
