"""Configuration handling for the FlyRank MCP server.

Credentials are loaded from environment variables, falling back to a
gitignored `.env` file next to the package. Precedence: process
environment > `.env` file. Nothing is ever written back, logged, or
exposed by the status tools.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

DEFAULT_BASE_URL = "https://internship.flyrank.ai"


@dataclass(frozen=True)
class FlyRankConfig:
    base_url: str
    cookie: str | None
    api_token: str | None
    state_dir: Path

    @property
    def auth_mode(self) -> str:
        if self.cookie:
            return "cookie"
        if self.api_token:
            return "bearer"
        return "none"

    @property
    def auth_configured(self) -> bool:
        return self.auth_mode != "none"

    def auth_headers(self) -> dict[str, str]:
        if self.cookie:
            return {"Cookie": self.cookie}
        if self.api_token:
            return {"Authorization": f"Bearer {self.api_token}"}
        return {}


def load_dotenv_file(path: Path) -> None:
    """Poor-man's dotenv: set env vars from a KEY=VALUE file if not already set."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_config(env_path: Path | None = None) -> FlyRankConfig:
    load_dotenv_file(env_path or ENV_PATH)
    base = os.environ.get("FLYRANK_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    if not base.startswith(("http://", "https://")):
        base = "https://" + base
    state = os.environ.get("FLYRANK_STATE_DIR") or str(Path.home() / ".flyrank-mcp")
    return FlyRankConfig(
        base_url=base,
        cookie=os.environ.get("FLYRANK_COOKIE") or None,
        api_token=os.environ.get("FLYRANK_API_TOKEN") or None,
        state_dir=Path(state),
    )


def with_state_dir(config: FlyRankConfig, state_dir: str | Path) -> FlyRankConfig:
    return replace(config, state_dir=Path(state_dir))