"""BE-08 · FastAPI endpoint that streams a generated PDF report.

    GET  /            -> API info
    GET  /stats       -> JSON summary of the underlying data
    GET  /report      -> 200 application/pdf (the generated report)
"""

from __future__ import annotations

from fastapi import FastAPI, Response

from report import DEFAULT_DATA, compute_stats, load_books, render_pdf_bytes

app = FastAPI(title="PDF Report Generator API", version="1.0.0")

_books = load_books(DEFAULT_DATA)


@app.get("/")
def root():
    return {"name": "PDF Report Generator API", "report": "/report", "stats": "/stats"}


@app.get("/stats")
def stats():
    return compute_stats(_books)


@app.get("/report")
def report():
    pdf = render_pdf_bytes(_books, source_display="data/books.json")
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="books-report.pdf"'},
    )
