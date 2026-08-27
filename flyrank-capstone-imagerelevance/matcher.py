"""Semantic embeddings + similarity ranking + mismatch guard.

Embeddings: lightweight deterministic bag-of-tokens hashing over subject + tags
(dimension 256). Cosine similarity for ranking. This is NOT a production model,
but it is a real, testable embedding + similarity pipeline; swap in a real
model (e.g. CLIP via Ollama) by replacing `embed()`.

Mismatch guard: even when ranking, reject a match when the predicted category
is too close to a different category (e.g. wolf vs fox) OR when confidence is
low. Rejections include an explanation.
"""

from __future__ import annotations

import math

DIM = 256


def embed(tokens) -> tuple:
    """Deterministic hashed bag-of-tokens embedding (unit vector)."""
    vec = [0.0] * DIM
    for tok in tokens:
        for t in str(tok).lower().split():
            h = abs(hash(t)) % DIM
            vec[h] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return tuple(v / norm for v in vec)


def cosine(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))


def tokenize(image) -> list:
    toks = [image.get("subject", ""), image.get("title", "")]
    toks += image.get("tags", [])
    return toks


# "confusing" category pairs that the guard watches (wolf vs fox)
CONFUSABLE = {frozenset(("wolf", "fox")), frozenset(("deer", "dog")),
              frozenset(("bear", "dog"))}


def _categories_overlap(a_cat, b_cat):
    if not a_cat or not b_cat:
        return False
    if a_cat == b_cat:
        return False
    return frozenset((a_cat.lower(), b_cat.lower())) in CONFUSABLE


class MatchResult:
    def __init__(self, image_id, score, category, confidence, accepted, reason=""):
        self.image_id = image_id
        self.score = round(score, 4)
        self.category = category
        self.confidence = round(confidence, 4)
        self.accepted = accepted
        self.reason = reason

    def to_dict(self):
        return {
            "image_id": self.image_id,
            "score": self.score,
            "category": self.category,
            "confidence": self.confidence,
            "accepted": self.accepted,
            "reason": self.reason,
        }


class Matcher:
    """Rank corpus by similarity to a query embedding; guard mismatches."""

    def __init__(self, catalog, threshold=0.12, low_conf_threshold=0.60):
        self.catalog = catalog
        self._emb = {e["id"]: embed(tokenize(e)) for e in catalog}
        self.threshold = threshold
        self.low_conf_threshold = low_conf_threshold

    def rank(self, query_vec):
        scored = sorted(
            ((cosine(query_vec, v), cid) for cid, v in self._emb.items()),
            key=lambda t: t[0],
            reverse=True,
        )
        return scored

    def match(self, vision_result):
        """Return top-1 ranked candidate (or None) with mismatch guard."""
        query_vec = embed(
            [vision_result.subject] + vision_result.tags
        )
        ranked = self.rank(query_vec)
        if not ranked:
            return None
        score, image_id = ranked[0]
        img = next(e for e in self.catalog if e["id"] == image_id)

        reason = ""
        # guard 1: low confidence -> flag, don't guess
        if vision_result.low_confidence:
            reason = "low confidence; not guessing"
        # guard 2: confusable category (wolf vs fox) with close score
        elif _categories_overlap(vision_result.category, img["category"]) and score < 0.3:
            reason = f"ambiguous: {vision_result.category} vs {img['category']}; possible mismatch"
        # guard 3: below absolute threshold
        elif score < self.threshold:
            reason = f"no confident match (score {score:.3f} below threshold)"
        # guard 4: predicted category disagrees sharply with top candidate
        elif vision_result.category and vision_result.category != img["category"]:
            reason = f"category mismatch: vision={vision_result.category}, corpus={img['category']}"

        accepted = not reason
        return MatchResult(
            image_id=image_id,
            score=score,
            category=img["category"],
            confidence=vision_result.confidence,
            accepted=accepted,
            reason=reason,
        )

    def explain(self, image_id):
        img = next((e for e in self.catalog if e["id"] == image_id), None)
        if not img:
            return None
        return {"image_id": image_id, "title": img["title"], "category": img["category"]}
