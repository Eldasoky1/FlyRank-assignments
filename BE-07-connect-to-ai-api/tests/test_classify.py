"""Tests for the AI classifier endpoint (BE-07).

All tests run OFFLINE using FakeLLM — no API key, no network, no cost.
They prove: strict schema enforcement, timeout & bounded-retry behaviour,
error handling, and the HTTP contract.

Run:
    pip install -r requirements.txt
    pytest tests/ -q
"""

import json

import pytest
from fastapi.testclient import TestClient

from llm import ClassificationError, Classifier, FakeLLM, _extract_json
from schemas import ClassificationRequest
import main

VALID = (
    '{"category": "technical", "sentiment": "negative", '
    '"confidence": 0.9, "tidy_subject": "Cannot login", '
    '"reasoning": "User reports auth failure."}'
)


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def fake():
    return FakeLLM(VALID)


def _install(fake):
    """Point the app at a controlled fake classifier."""
    main.classifier = Classifier(llm=fake, max_retries=2, backoff=0.0)


# ---- HTTP contract ----


def test_root(client):
    assert client.get("/").json()["name"] == "AI Classifier API"


def test_valid_classification_returns_200(client, fake):
    _install(fake)
    r = client.post("/classify", json={"message": "I cannot log in help"})
    assert r.status_code == 200
    assert r.json()["category"] == "technical"


def test_missing_message_422(client):
    r = client.post("/classify", json={})
    assert r.status_code == 422


def test_empty_message_422(client):
    r = client.post("/classify", json={"message": ""})
    assert r.status_code == 422


# ---- schema / parsing ----


def test_extract_json_ignores_markdown_fence():
    raw = '```json\n{"a": 1}\n```'
    assert _extract_json(raw) == {"a": 1}


def test_extract_json_embedded_in_surrounding_text():
    raw = 'Here you go: {"category": "sales", "confidence": 0.5} hope that helps'
    data = _extract_json(raw)
    assert data["category"] == "sales"


def test_extract_json_no_json_raises():
    with pytest.raises(ValueError):
        _extract_json("no json here at all")


# ---- timeout & retries ----


def test_non_json_output_retries_then_502(client, fake):
    fake.default = "I am a helpful chatbot, not JSON."
    _install(fake)
    r = client.post("/classify", json={"message": "hi"})
    assert r.status_code == 502
    assert fake.call_count == 3  # 1 initial + 2 retries, never infinite


def test_invalid_category_retries_then_502(client, fake):
    bad = '{"category": "nonsense", "sentiment": "neutral", "confidence": 0.5, "tidy_subject": "x y", "reasoning": "z"}'
    fake.default = bad
    _install(fake)
    r = client.post("/classify", json={"message": "hi"})
    assert r.status_code == 502
    assert fake.call_count == 3


def test_confidence_out_of_range_rejected(client, fake):
    bad = '{"category": "billing", "sentiment": "neutral", "confidence": 7.5, "tidy_subject": "x y", "reasoning": "z"}'
    fake.responses = [bad, VALID]  # first bad -> retry -> valid
    _install(fake)
    r = client.post("/classify", json={"message": "hi"})
    assert r.status_code == 200
    assert r.json()["category"] == "technical"


def test_retry_succeeds_after_one_bad_attempt(client, fake):
    fake.responses = ["this is not json", VALID]
    _install(fake)
    r = client.post("/classify", json={"message": "please fix my account"})
    assert r.status_code == 200
    assert r.json()["category"] == "technical"


def test_connection_error_surfaces_as_502():
    fake = FakeLLM(VALID)
    fake._fail_with = ConnectionError("timeout after 25s")
    classifier = Classifier(llm=fake, max_retries=1, backoff=0.0)
    with pytest.raises(ClassificationError):
        classifier.classify(ClassificationRequest(message="hi"))
    assert fake.call_count == 2  # bounded


def test_bounded_retries_never_infinite(client, fake):
    fake.default = "broken"
    _install(fake)
    # a huge max_retries would be slow; verify the loop stops at max_retries+1
    main.classifier = Classifier(llm=fake, max_retries=3, backoff=0.0)
    r = client.post("/classify", json={"message": "x"})
    assert r.status_code == 502
    assert fake.call_count == 4


# ---- classification helper ----


def test_classify_returns_model_on_first_success():
    fake = FakeLLM(VALID)
    classifier = Classifier(llm=fake, max_retries=2, backoff=0.0)
    out = classifier.classify(ClassificationRequest(message="hi"))
    assert out.category == "technical"
    assert out.confidence == 0.9
