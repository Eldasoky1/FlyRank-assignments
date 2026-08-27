"""BE-08 · PDF Report Generator.

Builds a professional PDF report from the scraped books catalogue
(see BE-05 -> `output/books.json`). Produces:

  * a title + metadata block,
  * summary statistics (count, catalogue value, avg price, rating mix),
  * a bar chart of average price per category,
  * a live rating distribution,
  * a paginated table of every book.

Pure-Python (ReportLab) — no system dependencies, works on any platform.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend

DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "books.json"

BRAND = colors.HexColor("#7C3AED")
LIGHT = colors.HexColor("#EDE9FE")
GRID = colors.HexColor("#E2E8F0")
INK = colors.HexColor("#1E293B")

CATEGORY_ORDER = ["billing", "technical", "account", "sales", "other"]


# ---------------------------------------------------------------- data load


def load_books(path: str | Path = DEFAULT_DATA) -> List[dict]:
    """Load the scraped books JSON (BE-05 format)."""
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    books = payload.get("books", payload if isinstance(payload, list) else [])
    if not isinstance(books, list):
        raise ValueError(f"unexpected books payload in {path}")
    return books


# ---------------------------------------------------------------- statistics


def compute_stats(books: Iterable[dict]) -> Dict[str, object]:
    books = list(books)
    total = sum(float(b.get("price_gbp", 0) or 0) for b in books)
    avg = (total / len(books)) if books else 0.0
    top = max(books, key=lambda b: float(b.get("price_gbp", 0) or 0)) if books else None
    return {
        "count": len(books),
        "total_value_gbp": round(total, 2),
        "avg_price_gbp": round(avg, 2),
        "max_price_gbp": round(float(top["price_gbp"]), 2) if top else 0.0,
        "top_title": top["title"] if top else "—",
    }


def average_price_by_category(books: Iterable[dict]) -> Dict[str, float]:
    buckets: Dict[str, List[float]] = {}
    for b in books:
        cat = str(b.get("category") or "other").lower()
        buckets.setdefault(cat, []).append(float(b.get("price_gbp", 0) or 0))
    return {
        cat: round(sum(v) / len(v), 2) for cat, v in sorted(buckets.items())
    }


def rating_distribution(books: Iterable[dict]) -> Dict[int, int]:
    return dict(
        sorted(
            Counter(int(b.get("rating", 0) or 0) for b in books).items(),
            key=lambda kv: kv[0],
        )
    )


# ---------------------------------------------------------------- chart help


def _bar_chart(avg: Dict[str, float]) -> Drawing:
    labels = list(avg.keys())
    values = [avg[k] for k in labels]
    draw = Drawing(470, 190)
    chart = VerticalBarChart()
    chart.x = 60
    chart.y = 40
    chart.width = 350
    chart.height = 120
    chart.data = [values]
    chart.strokeColor = None
    chart.categoryAxis.categoryNames = [l.title() for l in labels]
    chart.categoryAxis.labels.fontName = "Helvetica"
    chart.categoryAxis.labels.fontSize = 8
    chart.categoryAxis.labels.angle = 0
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = max(values) * 1.2
    chart.valueAxis.valueStep = 10
    chart.valueAxis.labelTextFormat = "£%0.0f"
    chart.bars[0].fillColor = BRAND
    chart.bars[0].strokeColor = None
    chart.barWidth = 26
    draw.add(chart)
    # value labels above bars
    for i, v in enumerate(values):
        x = chart.x + i * (chart.width / max(len(labels), 1)) + chart.barWidth / 2
        y = chart.y + chart.height + 4
        draw.add(
            String(x + 8, y, f"£{v:,.2f}", fontName="Helvetica-Bold", fontSize=8, fillColor=INK)
        )
    return draw


# ---------------------------------------------------------------- builder


class ReportBuilder:
    """Encapsulates the ReportLab document so tests can drive it directly."""

    def __init__(self, out_path, title: str = "Books Report"):
        # ReportLab accepts either a filename/path or a writeable file-like buffer.
        self.out_path = out_path if hasattr(out_path, "write") else Path(out_path)
        self.title = title
        self.styles = self._make_styles()

    def _make_styles(self):
        s = getSampleStyleSheet()
        title = ParagraphStyle(
            "BrandTitle",
            parent=s["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=INK,
            spaceAfter=2,
        )
        sub = ParagraphStyle(
            "BrandSub",
            parent=s["Normal"],
            textColor=colors.HexColor("#64748B"),
            fontSize=10,
            alignment=TA_LEFT,
        )
        h2 = ParagraphStyle(
            "BrandH2",
            parent=s["Heading2"],
            fontSize=13,
            textColor=BRAND,
            spaceBefore=10,
            spaceAfter=6,
        )
        return {"title": title, "sub": sub, "h2": h2}

    def _header(self) -> List:
        flow = [
            Paragraph(self.title, self.styles["title"]),
            Spacer(1, 4),
            Paragraph(
                f"Generated {self._now()} · data: {self.source_display}",
                self.styles["sub"],
            ),
            Spacer(1, 6),
            HRFlowable(width="100%", thickness=1.2, color=BRAND),
            Spacer(1, 8),
        ]
        return flow

    def _stats_block(self, stats: Dict[str, object]) -> List:
        cards = [
            ("Books", stats["count"]),
            ("Catalogue value", f"£{stats['total_value_gbp']:,.2f}"),
            ("Avg price", f"£{stats['avg_price_gbp']:,.2f}"),
            ("Top book", stats["top_title"]),
        ]
        data = [[Paragraph(f"<b>{k}</b>", self.styles["sub"]) for k, _ in cards]]
        data.append([Paragraph(str(v), self.styles["h2"]) for _, v in cards])
        tbl = Table(data, colWidths=[115] * 4)
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.7, GRID),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, GRID),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return [tbl, Spacer(1, 6)]

    def build(self, books: List[dict], source_display: str = "data/books.json") -> Path:
        self.source_display = source_display
        doc = SimpleDocTemplate(
            str(self.out_path),
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
            title="Books Report",
            author="FlyRank Assignments · BE-08",
        )
        doc.build(self._story(books))
        return self.out_path

    def _story(self, books: List[dict]) -> list:
        stats = compute_stats(books)
        avg = average_price_by_category(books)
        ratings = rating_distribution(books)

        story: list = [*self._header(), *self._stats_block(stats)]

        story.append(Paragraph("Average price by category", self.styles["h2"]))
        story.append(_bar_chart(avg))

        story.append(Paragraph("Rating distribution", self.styles["h2"]))
        story.append(self._rating_table(ratings))

        story.append(PageBreak())
        story.append(Paragraph("Catalogue", self.styles["h2"]))
        story.append(self._book_table(books))
        return story

    def _rating_table(self, ratings: Dict[int, int]) -> Table:
        rows = [["Rating", "Count", "Share"]]
        total = sum(ratings.values()) or 1
        for rating, count in ratings.items():
            share = f"{100 * count / total:.0f}%"
            rows.append([f"{rating} star(s)", str(count), share])
        tbl = Table(rows, colWidths=[120, 120, 120])
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BRAND),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, GRID),
                ]
            )
        )
        return tbl

    def _book_table(self, books: List[dict]) -> Table:
        header = ["Title", "Category", "Rating", "Price £"]
        rows = [header]
        for b in books:
            rows.append(
                [
                    Paragraph(self._ellipsize(b["title"], 44), self.styles["sub"]),
                    str(b.get("category", "")).title(),
                    "★" * int(b.get("rating", 0)),
                    f"{float(b.get('price_gbp', 0) or 0):,.2f}",
                ]
            )
        tbl = Table(rows, colWidths=[250, 100, 80, 65], repeatRows=1)
        tbl.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), INK),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 0.4, GRID),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ("ALIGN", (3, 0), (3, -1), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return tbl

    @staticmethod
    def _ellipsize(text: str, width: int) -> str:
        return text if len(text) <= width else text[: width - 1].rstrip() + "…"

    @staticmethod
    def _now() -> str:
        import datetime

        return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


def generate_report(
    books: List[dict],
    out_path: str | Path = "books-report.pdf",
    title: str = "Books Report",
    source_display: str = "data/books.json",
) -> Path:
    """One-call entry point: build the PDF and return its path."""
    return ReportBuilder(out_path, title=title).build(books, source_display=source_display)


def render_pdf_bytes(
    books: List[dict],
    title: str = "Books Report",
    source_display: str = "data/books.json",
) -> bytes:
    """Render the report straight to bytes (used by the HTTP endpoint)."""
    from io import BytesIO

    buf = BytesIO()
    builder = ReportBuilder(buf, title=title)
    builder.source_display = source_display
    SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Books Report",
        author="FlyRank Assignments · BE-08",
    ).build(builder._story(books))
    return buf.getvalue()
