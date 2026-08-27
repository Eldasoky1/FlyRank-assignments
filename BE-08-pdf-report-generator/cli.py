"""BE-08 · CLI for the PDF report generator.

Usage:
    python cli.py                          # default data -> books-report.pdf
    python cli.py --data data/books.json --out report.pdf --title "My Report"
"""

from __future__ import annotations

import argparse
import sys

from report import DEFAULT_DATA, generate_report, load_books


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate a PDF report of the books catalogue.")
    parser.add_argument("--data", default=str(DEFAULT_DATA), help="path to books JSON (BE-05 format)")
    parser.add_argument("--out", default="books-report.pdf", help="output PDF path")
    parser.add_argument("--title", default="Books Report", help="report title")
    args = parser.parse_args(argv)

    books = load_books(args.data)
    print(f"Loaded {len(books)} books from {args.data}")

    path = generate_report(books, out_path=args.out, title=args.title, source_display=args.data)
    print(f"Wrote {path} ({path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
