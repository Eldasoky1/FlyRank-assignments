"""Strict response schemas for the classification endpoint (BE-07).

The LLM is asked for a JUDGEMENT, never a chatbot answer. Every response must
conform to `Classification` — the endpoint enforces this by parsing the model's
JSON and validating it with Pydantic. Anything that cannot be coerced into this
schema is retried (a sane, bounded number of times) and finally rejected.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Category = Literal["billing", "technical", "account", "sales", "other"]
Sentiment = Literal["positive", "neutral", "negative"]


class ClassificationRequest(BaseModel):
    """Input: a raw support message to classify."""

    message: str = Field(min_length=1, max_length=4000)


class Classification(BaseModel):
    """Output: the structured judgement the model must return."""

    category: Category
    sentiment: Sentiment
    confidence: float = Field(ge=0, le=1)
    tidy_subject: str = Field(min_length=2, max_length=60)
    reasoning: str = Field(min_length=1, max_length=300)
