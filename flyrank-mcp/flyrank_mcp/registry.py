"""Persistent registry of endpoints discovered on the FlyRank portal.

Successful (2xx) requests made by the client are recorded under the
state directory (`~/.flyrank-mcp/endpoints.json` by default) so findings
survive MCP server restarts.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

REGISTRY_FILE = "endpoints.json"


def _registry_path(state_dir: Path) -> Path:
    return state_dir / REGISTRY_FILE


def load_registry(state_dir: Path) -> list[dict]:
    path = _registry_path(state_dir)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def record_endpoint(state_dir: Path, method: str, path: str, status: int) -> None:
    """Record a successful (2xx) endpoint hit, deduped on method+path."""
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        entries = load_registry(state_dir)
        key = f"{method.upper()} {path}"
        now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        for entry in entries:
            if f"{str(entry.get('method', '')).upper()} {entry.get('path', '')}" == key:
                entry["status"] = status
                entry["hits"] = int(entry.get("hits", 0)) + 1
                entry["last_seen"] = now
                break
        else:
            entries.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "status": status,
                    "hits": 1,
                    "first_seen": now,
                    "last_seen": now,
                }
            )
        _registry_path(state_dir).write_text(
            json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8"
        )
    except OSError:
        # Registry is best-effort; requests must not fail because of it.
        pass