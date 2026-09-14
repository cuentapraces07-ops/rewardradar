"""Strands tools that collect and verify bounty evidence."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict
from datetime import UTC, datetime
from html import unescape
from pathlib import Path
from typing import Any

from strands import tool

from .core import Candidate, assess_candidate, rank_candidates


HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "RewardRadar/0.3 (+https://github.com/cuentapraces07-ops/rewardradar)",
    "X-GitHub-Api-Version": "2022-11-28",
}

DEMO_FIXTURE = Path(__file__).parents[1] / "data" / "demo_candidates.json"
SUPERTEAM_FEED_URL = "https://superteam.fun/api/listings?take={limit}"
SUPERTEAM_DETAILS_URL = "https://superteam.fun/api/listings/details/{slug}"
SUPERTEAM_LISTING_URL = "https://superteam.fun/earn/listing/{slug}"
SUPERTEAM_AGENT_ACCESS = {"AGENT_ALLOWED", "AGENT_ONLY"}
USD_STABLE_TOKENS = {"USD", "USDC", "USDT"}


def _fetch_json(url: str) -> Any:
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def _deadline_is_future(value: Any, now: datetime | None = None) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        deadline = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    reference = now or datetime.now(UTC)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=UTC)
    return deadline > reference


def _usd_value(value: Any, token: Any) -> float | None:
    if not isinstance(value, (int, float)):
        return None
    if str(token or "").upper() not in USD_STABLE_TOKENS:
        return None
    return float(value)


def _superteam_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "listings", "items"):
        rows = payload.get(key)
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    return []


def _normalize_superteam_feed(
    payload: Any, now: datetime | None = None
) -> list[dict[str, Any]]:
    """Keep only open, agent-eligible listings and preserve payment-risk evidence."""

    normalized: list[dict[str, Any]] = []
    for row in _superteam_rows(payload):
        status = str(row.get("status") or "").upper()
        agent_access = str(row.get("agentAccess") or "").upper()
        deadline = row.get("deadline")
        if (
            status != "OPEN"
            or agent_access not in SUPERTEAM_AGENT_ACCESS
            or row.get("isWinnersAnnounced") is True
            or not _deadline_is_future(deadline, now=now)
        ):
            continue
        slug = str(row.get("slug") or "")
        counts = row.get("_count") or {}
        sponsor = row.get("sponsor") or {}
        normalized.append(
            {
                "source": "Superteam Earn",
                "title": row.get("title"),
                "url": SUPERTEAM_LISTING_URL.format(slug=slug),
                "slug": slug,
                "payout_usd": None,
                "advertised_reward_pool_usd": _usd_value(
                    row.get("rewardAmount"), row.get("token")
                ),
                "reward_amount": row.get("rewardAmount"),
                "payment_token": row.get("token"),
                "status": status,
                "agent_access": agent_access,
                "deadline": deadline,
                "submission_count": counts.get("Submission"),
                "comment_count": counts.get("Comments"),
                "sponsor": sponsor.get("name"),
                "sponsor_verified": sponsor.get("isVerified"),
                "foundation_paying": row.get("isFndnPaying"),
            }
        )
    return normalized


def _plain_html_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def _extract_superteam_requirements(
    description: Any, structured_deadline: Any = None
) -> dict[str, Any]:
    """Extract costly or identity-bound requirements without executing them."""

    text = _plain_html_text(description)
    trade_count_match = re.search(r"at least\s+(\d+)\s+qualifying trades", text, re.I)
    minimum_trade_match = re.search(
        r"(?:swaps? of at least|at least)\s+\$?([\d.]+)\s+USDC", text, re.I
    )
    close_day_match = re.search(
        r"(?:September|Septemper)\s+(\d{1,2})(?:st|nd|rd|th)?"
        r"\s*,?\s*\d{1,2}:\d{2}\s*UTC\s*:\s*competition closes",
        text,
        re.I,
    )
    structured_day = None
    if isinstance(structured_deadline, str):
        try:
            structured_day = datetime.fromisoformat(
                structured_deadline.replace("Z", "+00:00")
            ).day
        except ValueError:
            pass
    description_day = int(close_day_match.group(1)) if close_day_match else None
    return {
        "requires_x_account": bool(re.search(r"connect (?:your )?X account", text, re.I)),
        "requires_public_x_post": bool(re.search(r"public X post", text, re.I)),
        "requires_mainnet_trades": bool(re.search(r"Solana Mainnet", text, re.I)),
        "qualifying_trade_count": (
            int(trade_count_match.group(1)) if trade_count_match else None
        ),
        "minimum_single_trade_usdc": (
            float(minimum_trade_match.group(1)) if minimum_trade_match else None
        ),
        "description_close_day": description_day,
        "structured_deadline_day": structured_day,
        "deadline_conflict": (
            description_day is not None
            and structured_day is not None
            and description_day != structured_day
        ),
    }


@tool
def scan_opire(limit: int = 30) -> str:
    """Fetch current Opire reward rows. Returns normalized JSON with headline payout and competition counts.

    Args:
        limit: Maximum number of reward rows to return, between 1 and 100.
    """

    safe_limit = min(max(limit, 1), 100)
    rewards = _fetch_json("https://api.opire.dev/rewards")[:safe_limit]
    normalized = []
    for reward in rewards:
        normalized.append(
            {
                "source": "Opire",
                "title": reward.get("title", "Untitled reward"),
                "url": reward.get("url"),
                "payout_usd": (reward.get("pendingPrice") or {}).get("value", 0) / 100,
                "claimers": len(reward.get("claimerUsers") or []),
                "trying": len(reward.get("tryingUsers") or []),
                "bot_installed": bool((reward.get("project") or {}).get("isBotInstalled")),
            }
        )
    return json.dumps(normalized, sort_keys=True)


@tool
def load_demo_inventory() -> str:
    """Load the transparent, credential-free candidate fixture used by the reproducible demo."""

    return DEMO_FIXTURE.read_text(encoding="utf-8")


@tool
def verify_demo_inventory() -> str:
    """Verify the demo candidates' recorded canonical state and return an evidence ledger."""

    candidates = json.loads(DEMO_FIXTURE.read_text(encoding="utf-8"))
    evidence = [
        {
            "title": item["title"],
            "canonical_url": item["url"],
            "status": item["status"],
            "locked": item["locked"],
            "claimers": item["claimers"],
            "verification": "fixture replay; use verify_github_issue for a fresh live check",
        }
        for item in candidates
    ]
    return json.dumps(evidence, sort_keys=True)


@tool
def score_demo_inventory() -> str:
    """Execute the deterministic risk function over every transparent demo candidate."""

    candidates = [
        Candidate(**item)
        for item in json.loads(DEMO_FIXTURE.read_text(encoding="utf-8"))
    ]
    return json.dumps([assess_candidate(item).to_dict() for item in candidates], sort_keys=True)


@tool
def rank_demo_inventory() -> str:
    """Rank the transparent demo fixture and return the final evidence-backed decision queue."""

    candidates = [
        Candidate(**item)
        for item in json.loads(DEMO_FIXTURE.read_text(encoding="utf-8"))
    ]
    return json.dumps([decision.to_dict() for decision in rank_candidates(candidates)], sort_keys=True)


@tool
def scan_execution_market(limit: int = 100) -> str:
    """Fetch published Execution Market tasks and return normalized payout evidence.

    Args:
        limit: Maximum published tasks to request, between 1 and 100.
    """

    safe_limit = min(max(limit, 1), 100)
    payload = _fetch_json(
        f"https://api.execution.market/api/v1/tasks?status=published&limit={safe_limit}"
    )
    rows = payload.get("tasks") or payload.get("items") or payload.get("data") or []
    normalized = [
        {
            "source": "Execution Market",
            "title": row.get("title"),
            "url": row.get("url") or row.get("task_url"),
            "payout_usd": row.get("bounty_usd")
            or row.get("bounty")
            or row.get("reward")
            or row.get("price")
            or 0,
            "status": row.get("status"),
            "payment_network": row.get("payment_network"),
            "payment_token": row.get("payment_token"),
            "escrow_tx": row.get("escrow_tx"),
            "deadline": row.get("deadline"),
        }
        for row in rows
    ]
    return json.dumps(normalized, sort_keys=True)


@tool
def scan_superteam(limit: int = 100) -> str:
    """Fetch current Superteam listings and keep only open opportunities that allow agents.

    Args:
        limit: Maximum listings to request, between 1 and 100.
    """

    safe_limit = min(max(limit, 1), 100)
    payload = _fetch_json(SUPERTEAM_FEED_URL.format(limit=safe_limit))
    return json.dumps(_normalize_superteam_feed(payload), sort_keys=True)


@tool
def verify_superteam_listing(listing_url: str) -> str:
    """Verify a Superteam listing and expose social, capital, sponsor, and deadline risks.

    Args:
        listing_url: Full public Superteam Earn listing URL.
    """

    match = re.fullmatch(
        r"https://(?:earn\.)?superteam\.fun/(?:earn/)?listing/([a-z0-9-]+)",
        listing_url,
    )
    if not match:
        return json.dumps({"verified": False, "reason": "Unsupported listing URL"})
    slug = match.group(1)
    encoded_slug = urllib.parse.quote(slug, safe="-")
    try:
        listing = _fetch_json(SUPERTEAM_DETAILS_URL.format(slug=encoded_slug))
        feed = _fetch_json(SUPERTEAM_FEED_URL.format(limit=100))
    except urllib.error.HTTPError as exc:
        return json.dumps({"verified": False, "reason": f"Superteam HTTP {exc.code}"})
    except urllib.error.URLError as exc:
        return json.dumps({"verified": False, "reason": f"Superteam network error: {exc.reason}"})
    if not isinstance(listing, dict) or listing.get("slug") != slug:
        return json.dumps({"verified": False, "reason": "Listing payload mismatch"})

    feed_row = next((row for row in _superteam_rows(feed) if row.get("slug") == slug), {})
    counts = feed_row.get("_count") or {}
    rewards = listing.get("rewards") or {}
    stable_prizes = [
        value
        for value in rewards.values()
        if isinstance(value, (int, float))
        and str(listing.get("token") or "").upper() in USD_STABLE_TOKENS
    ]
    sponsor = listing.get("sponsor") or {}
    status = str(listing.get("status") or "").upper()
    agent_access = str(listing.get("agentAccess") or "").upper()
    requirements = _extract_superteam_requirements(
        listing.get("description"), listing.get("deadline")
    )
    result = {
        "verified": True,
        "canonical_url": SUPERTEAM_LISTING_URL.format(slug=slug),
        "status": status,
        "claimable_now": (
            status == "OPEN"
            and agent_access in SUPERTEAM_AGENT_ACCESS
            and listing.get("isWinnersAnnounced") is not True
            and _deadline_is_future(listing.get("deadline"))
        ),
        "agent_access": agent_access,
        "deadline": listing.get("deadline"),
        "advertised_reward_pool_usd": _usd_value(
            listing.get("rewardAmount"), listing.get("token")
        ),
        "individual_prize_floor_usd": min(stable_prizes) if stable_prizes else None,
        "individual_prize_ceiling_usd": max(stable_prizes) if stable_prizes else None,
        "payment_token": listing.get("token"),
        "submission_count": counts.get("Submission"),
        "sponsor": sponsor.get("name"),
        "sponsor_verified": sponsor.get("isVerified"),
        "foundation_paying": listing.get("isFndnPaying"),
        "payment_guarantee_verified": bool(listing.get("isFndnPaying")),
        **requirements,
    }
    return json.dumps(result, sort_keys=True)


@tool
def verify_github_issue(issue_url: str) -> str:
    """Cross-check a GitHub issue URL against GitHub's API instead of trusting a marketplace label.

    Args:
        issue_url: Full public GitHub issue URL in owner/repository/issues/number form.
    """

    match = re.fullmatch(r"https://github\.com/([^/]+)/([^/]+)/issues/(\d+)", issue_url)
    if not match:
        return json.dumps({"verified": False, "reason": "Unsupported issue URL"})
    owner, repository, number = match.groups()
    try:
        issue = _fetch_json(
            f"https://api.github.com/repos/{owner}/{repository}/issues/{number}"
        )
    except urllib.error.HTTPError as exc:
        return json.dumps({"verified": False, "reason": f"GitHub HTTP {exc.code}"})
    return json.dumps(
        {
            "verified": True,
            "state": issue.get("state"),
            "state_reason": issue.get("state_reason"),
            "locked": issue.get("locked"),
            "comments": issue.get("comments"),
            "updated_at": issue.get("updated_at"),
            "canonical_url": issue.get("html_url"),
        },
        sort_keys=True,
    )


@tool
def score_opportunity(candidate_json: str) -> str:
    """Apply RewardRadar's deterministic payment-probability and expected-value guardrails.

    Args:
        candidate_json: JSON object matching the Candidate fields in agent/core.py.
    """

    candidate = Candidate(**json.loads(candidate_json))
    return json.dumps(assess_candidate(candidate).to_dict(), sort_keys=True)


@tool
def rank_opportunities(candidates_json: str) -> str:
    """Rank a JSON list of normalized candidates by payment-adjusted hourly value.

    Args:
        candidates_json: JSON list of objects matching the Candidate fields.
    """

    candidates = [Candidate(**item) for item in json.loads(candidates_json)]
    return json.dumps([decision.to_dict() for decision in rank_candidates(candidates)], sort_keys=True)


TOOLS = [
    scan_opire,
    scan_execution_market,
    scan_superteam,
    verify_github_issue,
    verify_superteam_listing,
    score_opportunity,
    rank_opportunities,
    load_demo_inventory,
    verify_demo_inventory,
    score_demo_inventory,
    rank_demo_inventory,
]
