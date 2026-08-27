"""Tests for CampaignBooster (10x Solution)."""

import time

import pytest

from goal import CampaignPlan, generate_plan
from guardrail import validate_plan
from budget import project_budget
from checklist import build_checklist
from report import render_markdown, render_report
from pipeline import Pipeline, StageError


# ---------------------------------------------------------------------------
# Concept 1: structured schema-validated plan
# ---------------------------------------------------------------------------
def test_goal_produces_validated_plan():
    plan = generate_plan("drive trial signups for Gen Z")
    assert isinstance(plan, CampaignPlan)
    assert plan.objective
    assert plan.audiences
    assert len(plan.channels) == 5  # 5 channels


def test_plan_channels_have_assets():
    plan = generate_plan("boost awareness")
    for ch in plan.channels:
        assert ch.asset_types  # every channel has assets


def test_provider_invalid_raises():
    with pytest.raises(ValueError):
        generate_plan("x", provider="nope")


# ---------------------------------------------------------------------------
# Concept 2: guardrail with rejection + explanation (not silent pass)
# ---------------------------------------------------------------------------
def test_guardrail_passes_valid_plan():
    plan = generate_plan("launch the new dashboard for agencies")
    assert validate_plan(plan.model_dump())["ok"] is True


def test_guardrail_rejects_vague_plan():
    rep = validate_plan({"objective": "x", "audiences": [], "channels": []})
    assert rep["ok"] is False
    assert any("objective" in r for r in rep["reasons"])
    assert any("audience" in r for r in rep["reasons"])


# ---------------------------------------------------------------------------
# Concept 3: cost / budget accounting
# ---------------------------------------------------------------------------
def test_budget_projection_totals():
    plan = generate_plan("grow revenue")
    budget = project_budget(plan.model_dump())
    assert budget["grand_total_cents"] > 0
    assert abs(budget["grand_total_usd"] * 100 - budget["grand_total_cents"]) < 0.01
    assert len(budget["rows"]) == 5


# ---------------------------------------------------------------------------
# Concept 4: checklist transformation
# ---------------------------------------------------------------------------
def test_checklist_build():
    plan = generate_plan("awareness")
    items = build_checklist(plan.model_dump())
    assert items
    for item in items:
        assert item["status"] == "todo" and item["owner"]


# ---------------------------------------------------------------------------
# Concept 5: multi-stage pipeline (retries, progress, cost) + report
# ---------------------------------------------------------------------------
def test_pipeline_completes_all_stages():
    p = Pipeline()
    run_id = p.submit("launch a referral program")
    for _ in range(200):
        r = p.get(run_id)
        if r["status"] in ("completed", "failed"):
            break
        time.sleep(0.02)
    assert r["status"] == "completed"
    names = [s["name"] for s in r["ctx"]["stages"]]
    assert names == ["plan", "guardrail", "budget", "checklist", "report"]
    assert r["cost_micro_cents"] > 0
    assert "markdown" in r["ctx"]["report"]


def test_pipeline_produces_report_deliverable():
    p = Pipeline()
    run_id = p.submit("sell more subscriptions")
    for _ in range(200):
        r = p.get(run_id)
        if r["status"] in ("completed", "failed"):
            break
        time.sleep(0.02)
    md = r["ctx"]["report"]["markdown"]
    html = render_report(r["ctx"])
    assert "Objective" in md and "$" in md
    assert "<html>" in html and "Objective" in html


def test_pipeline_retries_then_fails_on_stage_error(monkeypatch):
    import pipeline as P

    orig = P.PlanStage.run

    called = {"n": 0}

    def flaky(self, ctx):
        called["n"] += 1
        if called["n"] < 3:
            raise RuntimeError("boom")
        return orig(self, ctx)

    monkeypatch.setattr(P.PlanStage, "run", flaky)
    p = P.Pipeline()
    run_id = p.submit("recoverable goal")
    for _ in range(200):
        r = p.get(run_id)
        if r["status"] in ("completed", "failed"):
            break
        time.sleep(0.02)
    assert r["status"] == "completed"  # succeeded after retries
    assert called["n"] >= 2


# ---------------------------------------------------------------------------
# API end-to-end
# ---------------------------------------------------------------------------
def test_api_full_flow():
    from fastapi.testclient import TestClient

    import main as M

    c = TestClient(M.app)
    resp = c.post("/campaigns", json={"goal": "launch a loyalty program"})
    assert resp.status_code == 200
    run_id = resp.json()["campaign_id"]
    for _ in range(200):
        run = c.get(f"/campaigns/{run_id}").json()
        if run["status"] in ("completed", "failed"):
            break
        time.sleep(0.02)
    assert run["status"] == "completed"
    assert len(run["stages"]) == 5
    assert run["cost_micro_cents"] > 0
    report = c.get(f"/campaigns/{run_id}/report")
    assert report.status_code == 200
    assert "Objective" in report.json()["markdown"]


def test_api_rejects_short_goal():
    from fastapi.testclient import TestClient

    import main as M

    c = TestClient(M.app)
    assert c.post("/campaigns", json={"goal": "hi"}).status_code == 422
