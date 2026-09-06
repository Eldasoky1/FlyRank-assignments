#!/usr/bin/env python3
"""FL-09 v2 eval: FL-06 suite E1-E6 (unchanged) + E7/E8 additions.
Assertions only - no nested subprocesses, no live feed bundle (E6 uses one
bogus feed with a 5s timeout). Real end-to-end runs are captured separately in
../FL-07-build-the-agent and in the FL-09 demo. Tee the output into
eval-results-v2.md."""

from __future__ import annotations

import shutil
import sys
import tempfile
from io import StringIO
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1] / "FL-07-build-the-agent"
sys.path.insert(0, str(AGENT_DIR))

import week_in_review as w  # noqa: E402

OUTFILE = Path(__file__).resolve().parent / "eval-results-v2.md"
_buf = StringIO()


def _emit(line: str) -> None:
    print(line)
    print(line, file=_buf)


fail = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global fail
    _emit(f"{name:<28}: {'PASS' if ok else 'FAIL'} {detail}")
    fail += 0 if ok else 1


# ---- E1-E6 (FL-06 spec, unchanged behaviour) -------------------------------------------
check(
    "E1 thin-run recovery",
    w.decide_topics([{"topics": ["security;breach"], "items_kept": 0, "ts": "2026-09-04T00:00:00+00:00"}], None)
    == ["appsec;cve;response"],
)

tmp = Path(tempfile.mkdtemp(prefix="fl09_"))
log = tmp / "w.md"
log.write_text("Delivered: merged #42\nBlocked: none\nNext: Metering\n", encoding="utf-8")

# E2 topic drift exercised WITHOUT the live bundle: override returns the term and
# the pipeline tolerates zero matches (search-only path mirrors the real run).
topics_override = w.decide_topics([], "keflavik-ropes")
check("E2 topic drift", topics_override == ["keflavik-ropes"])

it = w.synthesize([{"title": "t", "link": "https://x.example", "date": "", "excerpt": "hi there", "feed": "t"}])[0]
check("E3 hallucination guard", it.get("needs_review") is True)

b = w.draft({"delivered": ["x"], "blocked": [], "next": []}, [], ["t"])
check("E4 signoff gate", b.strip().endswith("*Ready for review — not submitted.*"))

check("E5 format contract", not w.lint(b)["missing_sections"] and w.lint(b)["under_500"])

_, failures = w.gather(["http://127.0.0.1:1/rss"], timeout=2)
check("E6 feed resilience", len(failures) >= 1)

# ---- E7/E8 (v2 additions) --------------------------------------------------------------
r7a = w.decide_topics([{"topics": ["LLM;AI"], "items_kept": 0, "ts": "2026-09-04T00:00:00+00:00"}], None)
r7b = w.decide_topics([{"topics": ["developer;api;launch"], "items_kept": 1, "ts": "2026-09-04T01:00:00+00:00"}], None)
check("E7 repeated thin weeks recover", r7a == ["regression;eval;automation"] and r7b == ["devtools;sdk;launch"])

b8 = w.draft({"delivered": ["x"], "blocked": [], "next": []}, [], ["t"])
check("E8 gate text in generated brief", "*Ready for review — not submitted.*" in b8)

shutil.rmtree(tmp, ignore_errors=True)

_emit(f"\nV2: {'ALL PASS' if fail == 0 else f'{fail} FAILURE(S)'}")
OUTFILE.write_text("# FL-09 v2 eval results\n\n" + _buf.getvalue(), encoding="utf-8")
raise SystemExit(1 if fail else 0)