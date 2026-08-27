"""LLM client for the classification endpoint (BE-07).

The endpoint calls a real LLM through an OpenAI-compatible API (any
free / no-credit-card provider such as Groq or OpenRouter via `base_url`).
The client enforces two crucial guarantees:

- TIMEOUT  — every model call has a hard timeout (default 25s). If the model
             does not answer in time, the call fails fast.
- RETRIES  — the raw model output is parsed and validated against the strict
             `Classification` schema. On a parse/validation failure or a
             transient error, we retry a *bounded* number of times with
             exponential backoff; we never retry forever (sane stop).

For offline tests a `FakeLLM` stands in for the provider, so the full flow
(including retries and failures) is verifiable without any credential.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Optional

from pydantic import ValidationError

from schemas import Classification, ClassificationRequest

log = logging.getLogger("ai-classifier")

SYSTEM_PROMPT = (
    "You classify support ticket messages. Return ONLY a single JSON object "
    "with exactly these keys and no extra text: "
    '{"category": "billing"|"technical"|"account"|"sales"|"other", '
    '"sentiment": "positive"|"neutral"|"negative", '
    '"confidence": <0.0 to 1.0>, '
    '"tidy_subject": "<2-6 word summary>", '
    '"reasoning": "<one short sentence>"}. '
    "Do not wrap it in markdown or code fences."
)


class ClassificationError(Exception):
    """Raised when classification ultimately fails (after retries)."""


class LLMClient:
    """Interface the endpoint depends on."""

    def complete(self, prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatLLM(LLMClient):
    """Real provider via the OpenAI SDK (Groq / OpenRouter / etc)."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: Optional[str] = None,
        timeout: float = 25.0,
    ):
        from openai import OpenAI

        self.model = model
        self.timeout = timeout
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def complete(self, prompt: str) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        return resp.choices[0].message.content or ""


class FakeLLM(LLMClient):
    """Deterministic fake used by tests.

    - `responses`: optional queue of raw strings to return per call.
    - `default`: raw string used when the queue is exhausted.
    Makes retry/failure behaviour fully testable offline.
    """

    def __init__(self, default="", responses: Optional[list] = None):
        self.default = default
        self.responses = list(responses or [])
        self.call_count = 0
        self._fail_with: Optional[Exception] = None

    def complete(self, prompt: str) -> str:
        self.call_count += 1
        if self._fail_with is not None:
            raise self._fail_with
        if self.responses:
            return self.responses.pop(0)
        return self.default


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of the model's raw text."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    # find the first { ... } block
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("no JSON object found in model output")
    return json.loads(cleaned[start : end + 1])


class Classifier:
    """Ties the client + schema + timeout + retries together."""

    def __init__(self, llm: LLMClient, max_retries: int = 2, backoff: float = 0.4):
        self.llm = llm
        self.max_retries = max_retries
        self.backoff = backoff

    def _prompt(self, message: str) -> str:
        return f'Classify this support message:\n"""\n{message}\n"""'

    def _attempt(self, prompt: str) -> Classification:
        raw = self.llm.complete(prompt)
        data = _extract_json(raw)
        return Classification(**data)

    def classify(self, request: ClassificationRequest) -> Classification:
        prompt = self._prompt(request.message)
        last_error: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                return self._attempt(prompt)
            except (ValidationError, ValueError, TypeError, ConnectionError) as exc:
                last_error = exc
                log.warning(
                    "classify attempt %d failed (%s); retrying…",
                    attempt + 1,
                    type(exc).__name__,
                )
                if attempt < self.max_retries:
                    time.sleep(self.backoff * (2 ** attempt))  # exponential backoff

        raise ClassificationError(
            f"model failed to produce a valid classification after "
            f"{self.max_retries + 1} attempts: {last_error}"
        )


def create_classifier() -> Classifier:
    """Factory: real provider when an API key is present, fake otherwise."""
    api_key = os.getenv("LLM_API_KEY")
    if api_key:
        llm = OpenAICompatLLM(
            api_key=api_key,
            model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
            base_url=os.getenv("LLM_BASE_URL"),
            timeout=float(os.getenv("LLM_TIMEOUT", "25")),
        )
    else:
        llm = FakeLLM()
    return Classifier(llm=llm, max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")))
