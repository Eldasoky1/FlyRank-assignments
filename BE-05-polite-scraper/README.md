# BE-05 · The Polite Scraper

A small, **polite** scraper that turns messy catalogue HTML from
[books.toscrape.com](https://books.toscrape.com) into **clean, validated
JSON** — 60 records, without ever being rude to the server.

**Language:** 🐍 Python — `requests` + `BeautifulSoup` + `pydantic`.

---

## What it does

1. Checks the site's `robots.txt` before touching anything and honours its
   `Disallow` rules.
2. Identifies itself with a descriptive **User-Agent**.
3. **Throttles** every request with a configurable polite delay.
4. Converts messy text fields (e.g. `"£51.77"`, `"Three"`, `"In stock (19 available)"`)
   into real typed values (floats, ints, booleans).
5. **Validates every record** against a Pydantic schema before accepting it.
6. **Never crashes** on a broken/missing page — it logs and continues.
7. Writes the final clean JSON artifact (`output/books.json`, 60 records).

---

## Project layout

```
BE-05-polite-scraper/
├── scraper.py          # the polite scraper (polite + resilient)
├── models.py           # the Pydantic validation schema (Book)
├── tests/test_scraper.py  # offline tests (fixtures, no network needed)
├── fixtures/           # sample HTML used by the tests
├── output/books.json   # final verified artifact — 60 clean records
└── README.md
```

---

## Approach

The scraper is built around a `PoliteScraper` class with an explicit,
documented politeness contract (each point maps to a requirement):

| Requirement | How it's implemented |
|-------------|----------------------|
| Check robots.txt | `confirm_robots_ok()` fetches `/robots.txt`, parses `Disallow`, and `get()` refuses any disallowed URL |
| Identify itself | A descriptive `User-Agent` is sent on every request |
| Throttle | `_throttle()` sleeps so there are `POLITE_DELAY` seconds between requests |
| Typed values | schema coerces `£51.77 → 51.77` (float), `Three → 3` (int), `In stock (n) → n` (int) + `in_stock` (bool) |
| Validate before accept | every page is built as a `Book` via Pydantic; invalid records are dropped |
| Broken/missing page | 404s and request failures are caught → logged → skipped, the run continues |
| 60 clean records | scrapes catalogue pages until 60 valid `Book`s are collected, then writes JSON |

### The schema (`models.py`)

Every field is validated:

```python
class Book(BaseModel):
    title: str                     # min_length=1
    upc: str
    price_gbp: float               # ≥ 0, coerced from "£51.77"
    price_excl_tax_gbp: float
    price_incl_tax_gbp: float
    tax_gbp: float
    rating: int                    # 1..5, coerced from "Three" → 3
    in_stock: bool                 # coerced from availability text
    availability_text: str
    availability_count: int        # "In stock (19 available)" → 19
    number_of_reviews: int
    category: str
    description: str
    product_url: str
```

### Error handling

- A 404 or network failure returns `None` from `get()`, which the scraper logs
  (`Page missing … skipping gracefully`) and moves on. The run never aborts.
- A record that fails schema validation is logged with the first error and
  **dropped** — the scraper keeps going until it has 60 valid records.
- A failure that survives retries is surfaced in the log so you can see exactly
  what was skipped and why.

### Politeness defaults

```text
POLITE_DELAY  = 2.0 s      between requests (default)
RETRY_LIMIT   = 2          attempts per page
BACKOFF       = 0.5 s      exponential backoff on 429/5xx
User-Agent    = PoliteScraper/1.0 (+repo URL; educational)
```

Retries use exponential backoff, respect `Retry-After`, and stop after a few
attempts — they never retry forever.

---

## How to run

```bash
cd BE-05-polite-scraper
python -m venv venv
venv\Scripts\activate            # or: source venv/bin/activate
pip install -r requirements.txt

# Scrape 60 books (3 catalogue pages) politely -> output/books.json
python scraper.py --pages 3 --target 60
```

CLI options:

| Flag | Default | Meaning |
|------|---------|---------|
| `--pages` | `3` | max catalogue pages to scrape |
| `--target` | `60` | number of books to collect |
| `--out` | `output/books.json` | output JSON path |
| `--delay` | `2.0` | seconds between requests (politeness) |
| `--retries` | `2` | retry attempts per page |
| `--backoff` | `0.5` | backoff factor |

`output/books.json` is already committed as the verified 60-record artifact.

---

## Running the tests (offline)

The tests use local fixture HTML, so they never hit the live site (which is
itself the polite thing to do — a test-suite must not hammer a practice
server).

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

Covers: currency→float coercion, rating words→int, availability→count/bool,
full fixture-page parsing, schema rejection of invalid records, robots.txt rule
parsing, disallowed-URL blocking, 404/network failure handling, catalogue URL
extraction, and throttle timing. Expected: `11 passed`.
