# BE-08 · PDF Report Generator

A small generator that turns the scraped books catalogue (BE-05) into a
**professional, multi-page PDF report** — complete with summary statistics, a
category price bar chart, a rating distribution, and a paginated table of all
60 books.

**Language:** 🐍 Python · **PDF engine:** ReportLab (pure Python, no system
dependencies).

---

## What you get

Running the generator on the real scraped data produces
`output/books-report.pdf` (≈10 KB, built from the 60-record catalogue). The
report contains:

1. **Title + metadata** — branded header, generated timestamp, data source.
2. **Summary cards** — book count, catalogue value, average price, top-priced title.
3. **Bar chart** — average price per category (drawn with ReportLab graphics).
4. **Rating distribution** — table of star-rating counts and shares.
5. **Book table** — every book with title, category, rating (★'s), price; paginated.

A committed sample is at `output/books-report.pdf`.

---

## Files

```
BE-08-pdf-report-generator/
├── report.py            # stats + ReportLab builder (cli.py & app.py share it)
├── cli.py               # command-line generator
├── app.py               # FastAPI endpoint that streams the PDF
├── data/books.json      # real scraped sample (60 books from BE-05)
├── output/books-report.pdf  # committed generated sample
├── tests/test_report.py # 13 offline tests
└── README.md
```

## Usage

### 1. CLI

```bash
cd BE-08-pdf-report-generator
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

python cli.py                                # default data -> books-report.pdf
python cli.py --data data/books.json \
              --out output/books-report.pdf \
              --title "Books Catalogue Report"
```

### 2. HTTP API

```bash
uvicorn app:app --port 8000
```

| Method | Path | Returns |
|--------|------|---------|
| GET | `/` | API info |
| GET | `/stats` | JSON summary of the data |
| GET | `/report` | `application/pdf` (downloadable) |

```bash
curl -o report.pdf http://localhost:8000/report
curl http://localhost:8000/stats
```

---

## How it works

- `load_books()` reads the BE-05 `books.json` payload (a Pydantic-validated
  scrape, so prices/ratings are already typed).
- `compute_stats()`, `average_price_by_category()`, `rating_distribution()`
  derive the report numbers from the data.
- `ReportBuilder` assembles the ReportLab *story* (flowables): a branded
  header, a stats table styled like cards, a `VerticalBarChart` with `£`
  value labels, a rating table, then a full book table with repeating header
  rows and zebra striping.
- The whole document handles pagination automatically via `SimpleDocTemplate`.

`cli.py` (filesystem) and `app.py` (HTTP) are thin wrappers around the same
`report.py` logic — `generate_report()` writes to disk,
`render_pdf_bytes()` returns the bytes for the API.

---

## Tests

```bash
pip install -r requirements.txt
python -m pytest tests/ -q
```

**13 tests**, all offline. Coverage:

- data loading returns the 60-book sample with the expected typed fields,
- a malformed JSON payload raises `ValueError`,
- statistics are correct (count, totals) and an empty list doesn't divide by
  zero,
- price-by-category and rating distributions are sane,
- the **real PDF output** is verified: starts with `%PDF`, ends with `%%EOF`,
  and is non-trivial in size (both `generate_report` and `render_pdf_bytes`),
- the HTTP contract: `/stats` returns JSON, `/report` returns
  `application/pdf`, `/` lists the routes.
