"""Image variant factory: produce per-platform size variants from a source.

For each target platform we define a size spec and a crop mode. make_variants
resizes an image with Pillow (letterboxed to the target box), producing a real,
deterministic variant on disk. variant_key gives a content+size hash used for
idempotence / dedup.
"""

from __future__ import annotations

import hashlib
import os

# platform -> (width, height, mode)
VARIANT_SPECS = {
    "facebook_feed": (1200, 630, "cover"),
    "twitter_card": (1600, 900, "cover"),
    "instagram_square": (1080, 1080, "cover"),
    "instagram_story": (1080, 1920, "contain"),
    "linkedin_feed": (1200, 627, "cover"),
    "youtube_thumb": (1280, 720, "cover"),
}


def source_hash(source_path: str) -> str:
    with open(source_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def variant_key(source_path: str, platform: str) -> str:
    return f"{source_hash(source_path)}-{platform}"


class Variant:
    def __init__(self, platform, width, height, out_path, mode, size_bytes, exists):
        self.platform = platform
        self.width = width
        self.height = height
        self.out_path = out_path
        self.mode = mode
        self.size_bytes = size_bytes
        self.exists = exists

    def to_dict(self):
        return {
            "platform": self.platform,
            "width": self.width,
            "height": self.height,
            "out_path": self.out_path,
            "mode": self.mode,
            "size_bytes": self.size_bytes,
            "exists": self_exists,
        }


def make_variants(source_path: str, out_dir: str, platforms=None) -> list[Variant]:
    from PIL import Image

    specs = {k: v for k, v in VARIANT_SPECS.items() if not platforms or k in platforms}
    os.makedirs(out_dir, exist_ok=True)
    src = Image.open(source_path)
    variants = []
    for platform, (w, h, mode) in specs.items():
        out_path = os.path.join(out_dir, f"{variant_key(source_path, platform)}.png")
        img = _fit(src, w, h, mode)
        if not os.path.exists(out_path):
            img.save(out_path)
        exists = os.path.exists(out_path)
        size = os.path.getsize(out_path) if exists else 0
        variants.append(Variant(platform, w, h, out_path, mode, size, exists))
    return variants


def _fit(img, width, height, mode):
    from PIL import Image as _I

    if mode == "cover":
        # scale to fully cover the box, then center-crop
        ratio = max(width / img.width, height / img.height)
        new = img.resize((round(img.width * ratio), round(img.height * ratio)), _I.LANCZOS)
        left = (new.width - width) // 2
        top = (new.height - height) // 2
        return new.crop((left, top, left + width, top + height))
    # contain: letterbox inside the box
    ratio = min(width / img.width, height / img.height)
    new = img.resize((round(img.width * ratio), round(img.height * ratio)), _I.LANCZOS)
    canvas = _I.new("RGB", (width, height), (255, 255, 255))
    offset = ((width - new.width) // 2, (height - new.height) // 2)
    canvas.paste(new, offset)
    return canvas
