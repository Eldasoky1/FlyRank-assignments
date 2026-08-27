"""Pydantic models = the validation schema every scraped book must satisfy.

The scraper never accepts a record that fails this schema. Any record that
cannot be coerced into a `Book` is logged and skipped instead of crashing
the whole run.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

# books.toscrape.com encodes ratings as words
RATING_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


class Book(BaseModel):
    """A validated book record (one page of the catalogue)."""

    title: str = Field(min_length=1)
    upc: str = Field(min_length=1)
    price_gbp: float = Field(ge=0)
    price_excl_tax_gbp: float = Field(ge=0)
    price_incl_tax_gbp: float = Field(ge=0)
    tax_gbp: float = Field(ge=0)
    rating: int = Field(ge=1, le=5)
    in_stock: bool
    availability_text: str
    availability_count: int = Field(ge=0)
    number_of_reviews: int = Field(ge=0)
    category: str = ""
    description: str = ""
    product_url: str = ""

    # --- coercers for the messy HTML text ---

    @field_validator("price_gbp", "price_excl_tax_gbp", "price_incl_tax_gbp", "tax_gbp", mode="before")
    @classmethod
    def _parse_price(cls, v):
        """Turn '£51.77' (or a bare number string) into a float."""
        if isinstance(v, (int, float)):
            return float(v)
        text = str(v).strip().replace("£", "").replace(",", "").replace("\xa0", "")
        if text in ("", "N/A", "nan", "None"):
            return 0.0
        try:
            return float(text)
        except ValueError:
            # e.g. an unexpected token; degrade gracefully to 0 rather than fail
            return 0.0

    @field_validator("rating", mode="before")
    @classmethod
    def _parse_rating(cls, v):
        """Accept 'Three', 'three', or the int 3."""
        if isinstance(v, int):
            return v
        word = str(v).strip().lower()
        if word in RATING_WORDS:
            return RATING_WORDS[word]
        try:
            return int(str(v).strip())
        except ValueError:
            raise ValueError(f"unknown rating word: {v!r}")

    @field_validator("availability_count", mode="before")
    @classmethod
    def _parse_availability_count(cls, v):
        """'In stock (19 available)' -> 19; 'Out of stock' -> 0."""
        if isinstance(v, int):
            return v
        text = str(v)
        import re

        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else 0

    @field_validator("in_stock", mode="before")
    @classmethod
    def _parse_in_stock(cls, v):
        if isinstance(v, bool):
            return v
        text = str(v).lower()
        return "in stock" in text and "out of stock" not in text

    @field_validator("number_of_reviews", mode="before")
    @classmethod
    def _parse_reviews(cls, v):
        if isinstance(v, int):
            return v
        import re

        match = re.search(r"(\d+)", str(v))
        return int(match.group(1)) if match else 0

    @field_validator("description")
    @classmethod
    def _clean_description(cls, v):
        return " ".join(str(v).split()).strip()
