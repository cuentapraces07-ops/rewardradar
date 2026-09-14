"""Capture an evidence snapshot from public reward and canonical issue APIs."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "RewardRadar/0.2 evidence-capture",
    "X-GitHub-Api-Version": "2022-11-28",
}


def fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def audit_opire() -> dict[str, Any]:
    rewards = fetch_json("https://api.opire.dev/rewards")
    audited: list[dict[str, Any]] = []
    for index, reward in enumerate(rewards):
        raw_url = reward.get("url") or ""
        match = re.fullmatch(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", raw_url)
        canonical: dict[str, Any] = {
            "verified": False,
            "state": "unverifiable",
            "reason": "non-standard GitHub issue URL",
        }
        if match:
            owner, repository, number = match.groups()
            try:
                issue = fetch_json(
                    f"https://api.github.com/repos/{owner}/{repository}/issues/{number}"
                )
                canonical = {
                    "verified": True,
                    "state": issue.get("state"),
                    "state_reason": issue.get("state_reason"),
                    "locked": issue.get("locked"),
                    "comments": issue.get("comments"),
                    "updated_at": issue.get("updated_at"),
                    "canonical_url": issue.get("html_url"),
                }
            except urllib.error.HTTPError as error:
                canonical = {
                    "verified": False,
                    "state": "unverifiable",
                    "reason": f"GitHub HTTP {error.code}",
                }
        payout = (reward.get("pendingPrice") or {}).get("value", 0) / 100
        audited.append(
            {
                "title": reward.get("title"),
                "marketplace_url": raw_url,
                "advertised_usd": payout,
                "claimers": len(reward.get("claimerUsers") or []),
                "trying": len(reward.get("tryingUsers") or []),
                "bot_installed": bool((reward.get("project") or {}).get("isBotInstalled")),
                "canonical": canonical,
            }
        )
        if index + 1 < len(rewards):
            time.sleep(0.12)

    open_rows = [row for row in audited if row["canonical"].get("state") == "open"]
    return {
        "endpoint": "https://api.opire.dev/rewards",
        "advertised_rows": len(audited),
        "canonical_open_rows": len(open_rows),
        "eliminated_or_unverifiable_rows": len(audited) - len(open_rows),
        "advertised_open_value_usd": round(sum(row["advertised_usd"] for row in open_rows), 2),
        "rows": audited,
    }


def audit_execution_market() -> dict[str, Any]:
    endpoint = "https://api.execution.market/api/v1/tasks?status=published&limit=100"
    payload = fetch_json(endpoint)
    rows = payload.get("tasks") or payload.get("items") or payload.get("data") or []

    def payout(row: dict[str, Any]) -> float:
        for key in ("bounty_usd", "bounty", "reward", "price", "amount", "budget"):
            value = row.get(key)
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, dict):
                nested = value.get("usd") or value.get("amount") or value.get("value")
                if isinstance(nested, (int, float)):
                    return float(nested)
        return 0.0

    normalized = [
        {
            "id": row.get("id"),
            "title": row.get("title"),
            "status": row.get("status"),
            "payout_usd": payout(row),
            "payment_network": row.get("payment_network"),
            "payment_token": row.get("payment_token"),
            "escrow_tx": row.get("escrow_tx"),
            "deadline": row.get("deadline"),
        }
        for row in rows
    ]
    return {
        "endpoint": endpoint,
        "published_rows": len(normalized),
        "published_value_usd": round(sum(row["payout_usd"] for row in normalized), 2),
        "rows": normalized,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = {
        "schema": "rewardradar.audit.v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "method": "Marketplace discovery followed by canonical GitHub verification",
        "opire": audit_opire(),
        "execution_market": audit_execution_market(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "opire_rows": payload["opire"]["advertised_rows"],
                "opire_open": payload["opire"]["canonical_open_rows"],
                "execution_market_rows": payload["execution_market"]["published_rows"],
                "execution_market_usd": payload["execution_market"]["published_value_usd"],
            }
        )
    )


if __name__ == "__main__":
    main()
