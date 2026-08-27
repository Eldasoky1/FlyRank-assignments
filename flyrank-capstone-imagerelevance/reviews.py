"""Review API store: approve/reject/inspect-why per image match decision."""

import threading
import time


class ReviewStore:
    def __init__(self):
        self._reviews = {}  # key: (image_id)
        self._lock = threading.Lock()

    def submit(self, image_id, match, vision):
        with self._lock:
            self._reviews[image_id] = {
                "image_id": image_id,
                "match": match,
                "vision": vision,
                "decision": "pending",
                "reviewed_at": None,
                "note": "",
            }
        return image_id

    def decision(self, image_id, approve: bool, note=""):
        with self._lock:
            rec = self._reviews.get(image_id)
            if not rec:
                return None
            rec["decision"] = "approved" if approve else "rejected"
            rec["note"] = note
            rec["reviewed_at"] = time.time()
            return rec

    def get(self, image_id):
        with self._lock:
            rec = self._reviews.get(image_id)
            return dict(rec) if rec else None

    def explain(self, image_id):
        """Inspect WHY a decision was made (match + vision + guard reason)."""
        rec = self.get(image_id)
        if not rec:
            return None
        return {
            "image_id": image_id,
            "decision": rec["decision"],
            "note": rec["note"],
            "match": rec["match"],
            "vision": rec["vision"],
            "why": rec["match"]["reason"] if rec["match"] else "no match produced",
        }
