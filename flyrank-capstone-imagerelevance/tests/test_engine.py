"""Tests for the AI Image Understanding & Content Matching Engine."""

import pytest

from corpus_data import CATEGORIES, CORPUS, by_category, by_id
from eval import EvalSet
from jobs import BatchRunner, JobStore
from matcher import Matcher, cosine, embed
from reviews import ReviewStore
from vision import GeminiVisionAdapter, MockVisionAdapter, VisionResult, build_adapter

from main import health


@pytest.fixture
def matcher():
    return Matcher(CORPUS)


@pytest.fixture
def mock_vision():
    return MockVisionAdapter(CORPUS)


# ---------------------------------------------------------------------------
# Corpus
# ---------------------------------------------------------------------------
def test_corpus_size_and_categories():
    assert len(CORPUS) >= 40
    assert set(CATEGORIES) == {"fox", "wolf", "dog", "bear", "deer"}
    for cat in CATEGORIES:
        assert len(by_category(cat)) >= 8  # 4+ categories, several each


def test_corpus_ids_are_global_unique():
    ids = [e["id"] for e in CORPUS]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Vision structured output (schema-validated, low-confidence flagged)
# ---------------------------------------------------------------------------
def test_mock_vision_returns_valid_result(mock_vision):
    img = by_id("fox-01")
    vr = mock_vision.describe(img)
    assert isinstance(vr, VisionResult)
    assert vr.category == "fox"
    assert 0.0 <= vr.confidence <= 1.0
    assert vr.low_confidence is False


def test_mock_vision_confidence_and_no_guess_flag():
    adapter = MockVisionAdapter(CORPUS)
    img = by_id("deer-02")
    vr = adapter.describe(img)
    assert vr.low_confidence is False  # not guessing


def test_vision_requires_api_key_for_gemini():
    g = GeminiVisionAdapter(api_key="")
    with pytest.raises(RuntimeError):
        g.describe(by_id("fox-01"))


def test_build_adapter_unknown_provider():
    with pytest.raises(ValueError):
        build_adapter("nope", CORPUS)


# ---------------------------------------------------------------------------
# Embeddings + similarity
# ---------------------------------------------------------------------------
def test_embed_is_unit_vector():
    v = embed(["red fox, crafty"])
    norm = sum(x * x for x in v) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_similar_tokens_rank_higher():
    a = embed(["fox", "red fox", "wild"])
    b = embed(["fox", "red fox"])
    c = embed(["grizzly bear", "brown bear"])
    assert cosine(a, b) > cosine(a, c)


def test_matcher_ranks_same_category_first(matcher):
    vr = MockVisionAdapter(CORPUS).describe(by_id("wolf-01"))
    ranked = matcher.rank(embed([vr.subject] + vr.tags))
    top_id = ranked[0][1]
    assert by_id(top_id)["category"] == "wolf"


# ---------------------------------------------------------------------------
# Mismatch guard (wolf vs fox -> explainable rejection)
# ---------------------------------------------------------------------------
def test_mismatch_guard_rejects_confusable(matcher):
    # force a low-confidence wolf result so the guard should reject rather than
    # confidently pick fox
    from vision import VisionResult

    vr = VisionResult(subject="grey wolf", category="wolf", tags=["wolf", "canid"],
                      confidence=0.3, low_confidence=True, summary="unclear")
    m = matcher.match(vr)
    # guard should refuse to guess on low confidence
    assert m is None or m.accepted is False


def test_match_accepts_high_confidence_same_category(matcher):
    vr = MockVisionAdapter(CORPUS).describe(by_id("dog-01"))
    m = matcher.match(vr)
    assert m is not None and m.accepted is True
    assert m.category == "dog"


@pytest.fixture
def match_context(matcher, mock_vision):
    return matcher, mock_vision


# ---------------------------------------------------------------------------
# Background job: retries + progress + cost
# ---------------------------------------------------------------------------
def test_batch_job_processes_and_tracks_cost(matcher, mock_vision):
    store = JobStore()
    runner = BatchRunner(store, matcher, mock_vision, workers=4)
    ids = [e["id"] for e in CORPUS[:8]]
    job_id = runner.submit(ids)
    job = store.get(job_id)
    # wait for completion
    import time

    for _ in range(50):
        job = store.get(job_id)
        if job["status"] in ("completed", "completed_with_errors"):
            break
        time.sleep(0.05)
    assert job["processed"] == 8
    assert job["status"] == "completed"
    assert job["cost_micro_cents"] > 0  # per-call cost tracked


def test_job_retries_on_provider_error(matcher):
    adapter = MockVisionAdapter(CORPUS, error_subjects={"red fox"})
    store = JobStore()
    runner = BatchRunner(store, matcher, adapter, workers=1)
    job_id = runner.submit(["fox-01", "dog-01"])
    import time

    for _ in range(50):
        job = store.get(job_id)
        if job["status"] in ("completed", "completed_with_errors"):
            break
        time.sleep(0.05)
    # fox-01 provider erred; job marked completed_with_errors, dog-01 succeeded
    assert job["status"] == "completed_with_errors"
    errs = [r for r in job["results"] if r.get("error")]
    oks = [r for r in job["results"] if "match" in r and r["match"]]
    assert len(errs) >= 1
    assert len(oks) >= 1


# ---------------------------------------------------------------------------
# Review API (approve / reject / inspect why)
# ---------------------------------------------------------------------------
def test_review_submit_decision_explain(matcher, mock_vision):
    rs = ReviewStore()
    img = by_id("bear-01")
    vr = mock_vision.describe(img)
    m = matcher.match(vr)
    rs.submit(img["id"], m.to_dict(), {"subject": vr.subject})
    assert rs.decision(img["id"], True, "looks right")["decision"] == "approved"
    expl = rs.explain(img["id"])
    assert expl["match"]["accepted"] is True
    assert expl["decision"] == "approved"


def test_reject_decision(matcher, mock_vision):
    rs = ReviewStore()
    img = by_id("deer-03")
    vr = mock_vision.describe(img)
    m = matcher.match(vr)
    rs.submit(img["id"], m.to_dict(), {"subject": vr.subject})
    rs.decision(img["id"], False, "not a deer")
    assert rs.explain(img["id"])["decision"] == "rejected"


# ---------------------------------------------------------------------------
# Eval set -> top-1 precision
# ---------------------------------------------------------------------------
def test_eval_reports_precision(matcher, mock_vision):
    es = EvalSet()
    report = es.run(matcher, mock_vision)
    assert report["labeled_count"] == 25
    assert report["accepted"] >= 20
    assert report["top1_precision"] >= 0.9


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
def test_health():
    assert health()["status"] == "ok"
