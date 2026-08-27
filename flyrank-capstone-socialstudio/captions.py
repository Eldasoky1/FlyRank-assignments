"""Caption composer: structured post data -> platform-specific copy.

Uses copywriting templates (hook / body / CTA) with optional placeholders
(hashtags, mentions, link). Pure functions, fully offline and testable.
"""

from __future__ import annotations

HOOKS = {
    "hook": "We're launching something big, {brand}!",
    "value": "Your {audience} deserve this.",
    "social": "Tag someone who needs to see this 👀",
}


class Caption:
    def __init__(self, text, platform, length):
        self.text = text
        self.platform = platform
        self.length = length

    def to_dict(self):
        return {"text": self.text, "platform": self.platform, "chars": self.length}


def compose(post: dict, platform: str) -> str:
    """Build a caption from a structured post dict."""
    brand = post.get("brand", "our studio")
    hook = post.get("hook", HOOKS["hook"]).format(brand=brand)
    body = post.get("body", "Meet " + post.get("product", "today's drop") + ".")
    cta = post.get("cta", "Link in bio.")
    hashtags = " ".join(f"#{h.strip('#').replace(' ', '_')}" for h in (post.get("hashtags") or []))
    text = f"{hook}\n\n{body}\n\n{cta}"
    text = f"{text}\n{hashtags}" if hashtags else text
    return text


def compose_for(post: dict, platform: str) -> Caption:
    text = compose(post, platform)
    # platform length limits (approx)
    limits = {
        "twitter_card": 280,
        "facebook_feed": 500,
        "linkedin_feed": 1300,
        "instagram_square": 2200,
        "instagram_story": 500,
        "youtube_thumb": 100,
    }
    limit = limits.get(platform, 500)
    result = text[:limit]
    # any clipping happens via truncation; if truncated add ellipsis marker
    if len(text) > limit:
        result = text[: limit - 1] + "…"
    return Caption(result, platform, len(result))
