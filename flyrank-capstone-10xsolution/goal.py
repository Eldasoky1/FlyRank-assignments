"""Goal -> structured campaign plan (schema-validated, mock provider).

Concept: structured schema-validated output. A one-line goal is turned into a
CampaignPlan (channels, audiences, asset types, budget split) validated by
Pydantic. The mock provider simulates an LLM planning pass offline; the
generator hook lets a real LLM be plugged in without changing consumers.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

SUPPORTED_CHANNELS = ["facebook", "instagram", "linkedin", "youtube", "x"]


class Audience(BaseModel):
    label: str
    note: str


class ChannelBrief(BaseModel):
    channel: str
    goal: str
    asset_types: list[str] = Field(default_factory=list)


class CampaignPlan(BaseModel):
    title: str
    objective: str
    audiences: list[Audience] = Field(default_factory=list)
    channels: list[ChannelBrief] = Field(default_factory=list)
    duration_weeks: int = 1
    priority: int = Field(ge=0, le=4, default=2)


def generate_plan(goal: str, provider="mock") -> CampaignPlan:
    """Turn a goal into a validated CampaignPlan. provider in {mock, gemini}."""
    if provider == "mock":
        return _mock_plan(goal)
    if provider == "gemini":
        return _llm_plan(goal)
    raise ValueError(f"unknown provider: {provider}")


def _mock_plan(goal: str) -> CampaignPlan:
    kw = goal.lower()
    audience = "gen-z" if any(w in kw for w in ("gen z", "young", "tiktok")) else "small business owners"
    channels = [] if "email" in kw else None
    briefs = [
        ChannelBrief(
            channel=c,
            goal=f"drive {goal.lower() or 'awareness'} on {c}",
            asset_types=_assets_for(c),
        )
        for c in SUPPORTED_CHANNELS
    ]
    return CampaignPlan(
        title="CampaignBooster plan",
        objective=goal,
        audiences=[Audience(label=audience, note="target segment")],
        channels=briefs,
        duration_weeks=2,
    )


def _assets_for(channel: str) -> list[str]:
    if channel in ("instagram", "facebook"):
        return ["hero", "carousel", "story"]
    return ["thumbnail", "video", "banner"]


def _llm_plan(goal: str) -> CampaignPlan:
    raise NotImplementedError("plug in Gemini/OpenAI to generate a plan")
