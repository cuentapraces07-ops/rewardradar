"""Fail-closed Ring API adapter for the optional Ring track variant.

No Ring credential is bundled or inferred. The adapter only performs a request
when the caller supplies an access token explicitly at runtime. This makes the
local project safe to test and leaves the simulator/device evidence gate
visible instead of fabricating Ring events.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class RingConfigurationError(RuntimeError):
    """Raised when a Ring runtime credential or endpoint is not configured."""


def _token_from_environment() -> str:
    token = os.environ.get("RING_ACCESS_TOKEN", "").strip()
    if not token:
        raise RingConfigurationError("RING_ACCESS_TOKEN is not configured")
    return token


def fetch_ring_json(path: str, *, token: str | None = None, base_url: str | None = None) -> Any:
    """Fetch one Ring API path without persisting the bearer token."""

    if not path.startswith("/") or ".." in path:
        raise ValueError("path must be a relative Ring API path")
    access_token = token or _token_from_environment()
    root = (base_url or os.environ.get("RING_API_BASE_URL", "")).rstrip("/")
    if not root.startswith("https://"):
        raise RingConfigurationError("RING_API_BASE_URL must be an HTTPS URL")
    request = urllib.request.Request(
        f"{root}{path}",
        headers={"Accept": "application/json", "Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RingConfigurationError(f"Ring API returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RingConfigurationError(f"Ring API unavailable: {exc.reason}") from exc


def runtime_status(*, token: str | None = None, base_url: str | None = None) -> dict[str, Any]:
    """Describe whether a real Ring runtime is configured; never claim device evidence."""

    try:
        _ = token or _token_from_environment()
        root = (base_url or os.environ.get("RING_API_BASE_URL", "")).rstrip("/")
        configured = root.startswith("https://")
    except RingConfigurationError:
        configured = False
    return {
        "track": "Ring",
        "runtime_configured": configured,
        "device_or_simulator_evidence": False,
        "disclosure": "A Ring API token and a simulator/device run are still required.",
    }
