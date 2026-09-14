"""Capture agent-eligible Superteam listings and their costly requirements."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.tools import (
    SUPERTEAM_DETAILS_URL,
    SUPERTEAM_FEED_URL,
    USD_STABLE_TOKENS,
    _extract_superteam_requirements,
    _fetch_json,
    _normalize_superteam_feed,
    _superteam_rows,
    _usd_value,
)


def audit_listing(row: dict[str, Any]) -> dict[str, Any]:
    details = _fetch_json(SUPERTEAM_DETAILS_URL.format(slug=row["slug"]))
    sponsor = details.get("sponsor") or {}
    rewards = details.get("rewards") or {}
    stable_prizes = [
        value
        for value in rewards.values()
        if isinstance(value, (int, float))
        and str(details.get("token") or "").upper() in USD_STABLE_TOKENS
    ]
    return {
        **row,
        "advertised_reward_pool_usd": _usd_value(
            details.get("rewardAmount"), details.get("token")
        ),
        "individual_prize_floor_usd": min(stable_prizes) if stable_prizes else None,
        "individual_prize_ceiling_usd": max(stable_prizes) if stable_prizes else None,
        "sponsor_verified": sponsor.get("isVerified"),
        "foundation_paying": details.get("isFndnPaying"),
        "payment_guarantee_verified": bool(details.get("isFndnPaying")),
        **_extract_superteam_requirements(
            details.get("description"), details.get("deadline")
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    endpoint = SUPERTEAM_FEED_URL.format(limit=100)
    feed = _fetch_json(endpoint)
    open_agent_rows = _normalize_superteam_feed(feed)
    audited = [audit_listing(row) for row in open_agent_rows]
    payload = {
        "schema": "rewardradar.superteam-audit.v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "endpoint": endpoint,
        "feed_rows": len(_superteam_rows(feed)),
        "open_agent_eligible_rows": len(audited),
        "rows": audited,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "feed_rows": payload["feed_rows"],
                "open_agent_eligible_rows": payload["open_agent_eligible_rows"],
            }
        )
    )


if __name__ == "__main__":
    main()
