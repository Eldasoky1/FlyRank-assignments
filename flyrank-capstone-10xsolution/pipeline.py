"""Pipeline: multi-stage orchestration with retries, progress, and cost.

Concept: multi-stage pipeline orchestration (from job-runner patterns). A
campaign goal flows through stages: plan -> guardrail -> budget -> checklist ->
report. Each stage routes input to output; the orchestrator runs stages off the
request path, retries transient failures, reports progress, and accumulates
per-stage cost.
"""

from __future__ import annotations

import threading
import time
import uuid

from goal import generate_plan
from guardrail import validate_plan
from budget import project_budget
from checklist import build_checklist
from report import render_report, render_markdown

MAX_RETRIES = 2


class StageError(Exception):
    pass


class Stage:
    """A named pipeline stage. run(ctx) -> output dict. cost in micro-cents."""

    name = "stage"
    cost_micro_cents = 1

    def run(self, ctx):
        raise NotImplementedError


class PlanStage(Stage):
    name = "plan"
    cost_micro_cents = 8

    def run(self, ctx):
        plan = generate_plan(ctx["goal"], provider=ctx.get("provider", "mock"))
        return plan.model_dump()


class GuardrailStage(Stage):
    name = "guardrail"

    def run(self, ctx):
        return validate_plan(ctx["plan"])


class BudgetStage(Stage):
    name = "budget"

    def run(self, ctx):
        budget = project_budget(ctx["plan"])
        return {"channels": budget["rows"], "grand_total_cents": budget["grand_total_cents"],
                "grand_total_usd": budget["grand_total_usd"]}


class ChecklistStage(Stage):
    name = "checklist"

    def run(self, ctx):
        return build_checklist(ctx["plan"])


class ReportStage(Stage):
    name = "report"

    def run(self, ctx):
        return {"markdown": render_markdown(ctx), "html": render_report(ctx)}


class Pipeline:
    """Runs stages in order, with per-stage retries and progress + cost."""

    def __init__(self):
        self._runs = {}
        self._lock = threading.Lock()

    def submit(self, goal: str, provider="mock"):
        run_id = uuid.uuid4().hex[:8]
        with self._lock:
            self._runs[run_id] = {
                "id": run_id,
                "goal": goal,
                "status": "queued",
                "ctx": {"goal": goal, "provider": provider, "stages": []},
                "cost_micro_cents": 0,
                "error": None,
            }
        t = threading.Thread(target=self._execute, args=(run_id,), daemon=True)
        t.start()
        return run_id

    def _execute(self, run_id):
        stages = [PlanStage(), GuardrailStage(), BudgetStage(), ChecklistStage(), ReportStage()]
        self._mark(run_id, "running")
        for stage in stages:
            try:
                out = self._run_stage(run_id, stage)
            except StageError as exc:
                self._mark(run_id, "failed", error=str(exc))
                return
            with self._lock:
                ctx = self._runs[run_id]["ctx"]
                ctx[stage.name] = out
                ctx["stages"].append({"name": stage.name, "ok": True,
                                      "cost_micro_cents": stage.cost_micro_cents})
                self._runs[run_id]["cost_micro_cents"] += stage.cost_micro_cents
        self._mark(run_id, "completed")

    def _run_stage(self, run_id, stage):
        last = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                with self._lock:
                    ctx = dict(self._runs[run_id]["ctx"])
                return stage.run(ctx)
            except Exception as exc:  # noqa: BLE001
                last = exc
                if attempt < MAX_RETRIES:
                    time.sleep(0.02 * (attempt + 1))
        raise StageError(f"{stage.name}: {last}")

    def _mark(self, run_id, status, error=None):
        with self._lock:
            if run_id in self._runs:
                self._runs[run_id]["status"] = status
                if error:
                    self._runs[run_id]["error"] = error

    def get(self, run_id):
        with self._lock:
            r = self._runs.get(run_id)
            return dict(r) if r else None
