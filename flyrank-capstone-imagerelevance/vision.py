"""Vision provider adapter with STRICT structured output.

The brief demands schema-validated structured output where low-confidence
results are FLAGGED, not guessed. Every adapter returns a pydantic-validated
VisionResult; a failing/schema-invalid call raises and is handled by the job
layer (retry). Confidence is always explicit.

Providers: mock (offline default), gemini (Google Flash, free tier), ollama
(local, free). The mock provider simulates deterministic, costed output.
"""

from __future__ import annotations

import time
from typing import List, Optional

from pydantic import BaseModel, Field


class VisionResult(BaseModel):
    """Strict structured output from the vision model."""

    subject: str = Field(description="primary subject label")
    category: str | None = Field(default=None, description="predicted category")
    tags: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    low_confidence: bool = Field(default=False, description="true when model is unsure")
    summary: str = Field(default="")


class VisionAdapter:
    """Interface. Subclasses implement describe(image_id) -> VisionResult."""

    def describe(self, image) -> VisionResult:
        raise NotImplementedError

    def cost_cents(self) -> int:
        raise NotImplementedError


class MockVisionAdapter(VisionAdapter):
    """Deterministic provider for offline tests/demo. Simulates a vision call
    that correctly identifies the category and charges a fixed per-call cost."""

    per_call_cents = 0.2

    def __init__(self, catalog, error_subjects: Optional[set] = None):
        self.catalog = catalog
        self.error_subjects = error_subjects or set()

    def describe(self, image) -> VisionResult:
        time.sleep(0.001)  # simulate latency
        if image["title"] in self.error_subjects:
            raise RuntimeError("provider boom")
        # correct category with a high but not perfect confidence
        return VisionResult(
            subject=image["title"],
            category=image["category"],
            tags=image["alt_tags"],
            confidence=0.92,
            low_confidence=False,
            summary=f"a {image['title']}",
        )

    def cost_cents(self) -> int:
        return self.per_call_cents  # fractional; tracked in micro-cost separately


class GeminiVisionAdapter(VisionAdapter):
    """Google Gemini Flash (free tier). Requires GEMINI_API_KEY + model."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash", per_call_cents: int = 0):
        self.api_key = api_key
        self.model = model
        self.per_call_cents = per_call_cents

    def describe(self, image) -> VisionResult:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not configured")
        import httpx

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": "Identify the subject. Return a single JSON object with "
                                 "subject, category (fox|wolf|dog|bear|deer), tags[], "
                                 "confidence 0-1, low_confidence bool, summary."},
                        {"inline_data": {"mime_type": "image/jpeg", "data": ""}},
                    ]
                }
            ],
            "generationConfig": {"response_mime_type": "application/json"},
        }
        resp = httpx.post(url, params={"key": self.api_key}, json=payload, timeout=30)
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        parsed = _safe_parse_json(text)
        return VisionResult.model_validate(parsed)

    def cost_cents(self) -> int:
        return self.per_call_cents


class OllamaVisionAdapter(VisionAdapter):
    """Local Ollama (free) with an llava-class multimodal model."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llava",
                 per_call_cents: int = 0):
        self.base_url = base_url
        self.model = model
        self.per_call_cents = per_call_cents

    def describe(self, image) -> VisionResult:
        import httpx

        resp = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": 'Answer as JSON: {"subject":..., "category": fox|wolf|dog|bear|deer, "confidence": 0-1}',
                "images": [image.get("b64", "")],
                "format": "json",
                "stream": False,
            },
            timeout=60,
        )
        resp.raise_for_status()
        parsed = _safe_parse_json(resp.json()["response"])
        return VisionResult.model_validate(parsed)

    def cost_cents(self) -> int:
        return self.per_call_cents


def _safe_parse_json(text: str) -> dict:
    import json

    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def build_adapter(provider: str, catalog, config=None) -> VisionAdapter:
    config = config or {}
    if provider == "mock":
        return MockVisionAdapter(catalog)
    if provider == "gemini":
        return GeminiVisionAdapter(api_key=config.get("api_key", ""))
    if provider == "ollama":
        return OllamaVisionAdapter(
            base_url=config.get("base_url", "http://localhost:11434"),
            model=config.get("model", "llava"),
        )
    raise ValueError(f"unknown vision provider: {provider}")
