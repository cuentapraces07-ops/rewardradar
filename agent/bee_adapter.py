"""Import boundary for real Bee exports, with no synthetic live-data claim."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class BeeDataError(ValueError):
    """Raised when a Bee export is missing or not a supported JSON object."""


def load_bee_export(path: str | Path) -> dict[str, Any]:
    """Load an owner-supplied Bee/Apple Watch export without contacting Bee."""

    export_path = Path(path)
    if not export_path.is_file():
        raise BeeDataError("Bee export path does not exist")
    try:
        value = json.loads(export_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BeeDataError("Bee export is not valid JSON") from exc
    if not isinstance(value, dict):
        raise BeeDataError("Bee export must be a JSON object")
    return value


def runtime_status(path: str | Path | None = None) -> dict[str, Any]:
    """Report whether a real export is present; never call fixture data live Bee data."""

    available = bool(path and Path(path).is_file())
    return {
        "track": "Bee",
        "runtime_configured": available,
        "live_device_evidence": available,
        "disclosure": "Bee track requires data recorded by a Bee device or Apple Watch.",
    }
