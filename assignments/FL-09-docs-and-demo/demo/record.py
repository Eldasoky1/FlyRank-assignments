#!/usr/bin/env python3
"""FL-09 demo recorder: renders demo.html in headless Edge and records a screen video.

Usage:
    python record.py --out demo.webm --seconds 205
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from playwright.sync_api import sync_playwright


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="demo.webm")
    ap.add_argument("--seconds", type=int, default=205)
    args = ap.parse_args()

    html = (Path(__file__).resolve().parent / "demo.html").as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        ctx = browser.new_context(record_video_dir=str(Path(__file__).resolve().parent / ".rec"), viewport={"width": 1280, "height": 720})
        page = ctx.new_page()
        page.goto(html, timeout=30000)
        page.wait_for_timeout(1500)  # stage-ready caption
        time.sleep(args.seconds)
        page.wait_for_selector("#gate", state="visible", timeout=10000)
        page.wait_for_timeout(4000)  # let the guardrail card settle on camera
        ctx.close()  # finalizes the recording
        browser.close()

    vids = sorted((Path(__file__).resolve().parent / ".rec").glob("*.webm"))
    if not vids:
        raise SystemExit("no video produced")
    out = Path(args.out)
    vids[-1].rename(out)
    print(f"demo video -> {out} ({out.stat().st_size / 1e6:.1f} MB, {args.seconds + 6}s)")


if __name__ == "__main__":
    main()