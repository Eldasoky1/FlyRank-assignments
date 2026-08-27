"""Labeled eval set + top-1 precision measurement.

Builds a labeled eval set (image_id -> ground-truth category) from the corpus,
runs the vision adapter + matcher, and computes top-1 precision: the fraction
of accepted matches whose predicted category equals the ground truth.
Mismatch-guard rejections are counted separately (they are "refused, not
wrong"), which is the point of the guard.
"""

from __future__ import annotations

from corpus_data import CORPUS, by_id


class EvalSet:
    def __init__(self, images=None):
        # labeled subset: choose 5 per category for the eval set
        self.images = images or _default_eval()

    def run(self, matcher, vision_adapter):
        correct = 0
        accepted = 0
        rejected = 0
        wrong = 0
        rejected_reasons = {}
        for img in self.images:
            vr = vision_adapter.describe(img)
            m = matcher.match(vr)
            if m is None or not m.accepted:
                rejected += 1
                reason = (m.reason if m else "no match")
                rejected_reasons[reason] = rejected_reasons.get(reason, 0) + 1
                continue
            accepted += 1
            if m.category == img["category"]:
                correct += 1
            else:
                wrong += 1
        precision = (correct / accepted) if accepted else 0.0
        return {
            "labeled_count": len(self.images),
            "accepted": accepted,
            "rejected": rejected,
            "rejected_reasons": rejected_reasons,
            "correct": correct,
            "wrong": wrong,
            "top1_precision": round(precision, 4),
        }


def _default_eval():
    # 5 per category -> 25 labeled images
    per_cat = {}
    for e in CORPUS:
        per_cat.setdefault(e["category"], []).append(e)
    chosen = []
    for cat, items in per_cat.items():
        chosen.extend(items[:5])
    return chosen
