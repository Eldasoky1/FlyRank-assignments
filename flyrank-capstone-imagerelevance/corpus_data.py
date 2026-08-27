"""Image corpus: 50 images across 5 categories (fox, wolf, dog, bear, deer).

Images are free (Unsplash/Pexels) referenced by URL; the engine works on the
metadata + a placeholder image blob so it runs fully offline and at $0.
Each entry has ground-truth label(s) used by the eval set.
"""

import json
import os

CATEGORIES = ["fox", "wolf", "dog", "bear", "deer"]

# Each: {id, category, title, src (url or local path), alt_tags, label}
_CORPUS = []

_templates = {
    "fox": ["red fox", "arctic fox", "fennec fox", "fox kit", "fox in snow"],
    "wolf": ["grey wolf", "timber wolf", "wolf howling", "wolf pack", "arctic wolf"],
    "dog": ["golden retriever", "husky", "labrador", "shepherd", "poodle"],
    "bear": ["grizzly bear", "polar bear", "brown bear", "black bear", "cub"],
    "deer": ["whitetail deer", "elk", "caribou", "fawn", "stags"],
}

_nonce = 0
for cat in CATEGORIES:
    for i in range(10):
        title = _templates[cat][i % 5]
        _CORPUS.append(
            {
                "id": f"{cat}-{i+1:02d}",
                "category": cat,
                "title": title,
                "src": f"https://images.unsplash.com/photo-{7000 + _nonce}?w=400",
                "alt_tags": [title] + [f"{cat}"],
                "label": cat,
            }
        )
        _nonce += 1

CORPUS = _CORPUS


def corpus_path() -> str:
    return os.path.join(os.path.dirname(__file__), "corpus", "images.json")


def dump_corpus():
    if not os.path.exists(os.path.dirname(corpus_path())):
        os.makedirs(os.path.dirname(corpus_path()))
    with open(corpus_path(), "w", encoding="utf-8") as f:
        json.dump(CORPUS, f, indent=2)
    return len(CORPUS)


def by_id(image_id):
    for e in CORPUS:
        if e["id"] == image_id:
            return e
    return None


def by_category(cat):
    return [e for e in CORPUS if e["category"] == cat]
