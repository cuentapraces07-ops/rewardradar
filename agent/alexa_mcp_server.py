"""Credential-free Streamable HTTP MCP server for an Alexa+ prototype.

The server deliberately serves the checked-in RewardRadar fixture. It is a
small, inspectable prototype for the Alexa+ track: no AWS credentials, account
tokens, payout keys, or personal data are read. A production deployment would
put this endpoint behind HTTPS and replace the fixture adapter with the live
source adapters after reviewing their authentication and rate limits.

Run it with::

    python -m agent.alexa_mcp_server --port 8787

The MCP endpoint is ``POST /mcp``. It handles the JSON-RPC methods needed by a
minimal client: ``initialize``, ``notifications/initialized``, ``tools/list``,
and ``tools/call``.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import secrets
import threading
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from .core import Candidate, assess_candidate, rank_candidates


# Keep this endpoint dependency-free so judges can reproduce the MCP protocol
# without installing the optional Strands runtime first.
DEMO_FIXTURE = Path(__file__).parents[1] / "data" / "demo_candidates.json"


PROTOCOL_VERSION = "2025-11-25"
SERVER_INFO = {"name": "rewardradar-alexa-plus", "version": "0.2.1"}


class CaseStore:
    """A tiny, memory-only casefile store for one local MCP server process.

    The store deliberately keeps only public fixture-derived evidence. It has
    no account, user, credential, or network identity, and it expires entries
    instead of writing context to disk. A client can resume a case after a new
    MCP initialize/reconnect only while the same local server process is live.
    """

    def __init__(
        self,
        *,
        ttl_seconds: float = 15 * 60,
        max_cases: int = 32,
        clock: Callable[[], float] | None = None,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if max_cases < 1:
            raise ValueError("max_cases must be at least one")
        self.ttl_seconds = float(ttl_seconds)
        self.max_cases = int(max_cases)
        self._clock = clock or time.monotonic
        self._cases: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def _prune(self, now: float) -> None:
        for case_id, entry in list(self._cases.items()):
            if entry["expires_at"] <= now:
                del self._cases[case_id]

    def create(self, snapshot: dict[str, Any]) -> tuple[str, int]:
        """Store one JSON-like fixture snapshot and return an opaque case id."""

        now = self._clock()
        with self._lock:
            self._prune(now)
            while len(self._cases) >= self.max_cases:
                oldest = min(self._cases, key=lambda case_id: self._cases[case_id]["created_at"])
                del self._cases[oldest]
            case_id = uuid.uuid4().hex
            self._cases[case_id] = {
                "created_at": now,
                "expires_at": now + self.ttl_seconds,
                "snapshot": copy.deepcopy(snapshot),
            }
        return case_id, int(self.ttl_seconds)

    def get(self, case_id: Any) -> dict[str, Any] | None:
        """Return a copy of a live case, without exposing store internals."""

        if not isinstance(case_id, str) or len(case_id) != 32:
            return None
        now = self._clock()
        with self._lock:
            self._prune(now)
            entry = self._cases.get(case_id)
            if entry is None:
                return None
            return copy.deepcopy(entry["snapshot"])


DEFAULT_CASE_STORE = CaseStore()


def _fixture_digest() -> str:
    """Version evidence cases against the exact checked-in fixture bytes."""

    return hashlib.sha256(DEMO_FIXTURE.read_bytes()).hexdigest()


def _fixture_candidates() -> list[Candidate]:
    payload = json.loads(DEMO_FIXTURE.read_text(encoding="utf-8"))
    return [Candidate(**item) for item in payload]


def _matching_candidates(query: str) -> list[Candidate]:
    """Return fixture rows matching a voice-safe title/source query."""

    candidates = _fixture_candidates()
    if not query:
        return candidates
    return [
        candidate
        for candidate in candidates
        if query in f"{candidate.title} {candidate.source}".lower()
    ]


def _result_text(value: Any) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(value, sort_keys=True)}],
        "structuredContent": value,
    }


def _search_rewards(arguments: dict[str, Any]) -> dict[str, Any]:
    query = str(arguments.get("query") or "").strip().lower()
    try:
        limit = min(max(int(arguments.get("limit", 5)), 1), 20)
    except (TypeError, ValueError):
        limit = 5
    candidates = _matching_candidates(query)
    decisions = rank_candidates(candidates)[:limit]
    return {
        "mode": "fixture",
        "query": query,
        "results": [decision.to_dict() for decision in decisions],
        "disclosure": "Fixture replay; use the live adapters for fresh evidence.",
    }


def _verify_funding(arguments: dict[str, Any]) -> dict[str, Any]:
    title = str(arguments.get("title") or "").strip().lower()
    candidates = _fixture_candidates()
    candidate = next((item for item in candidates if item.title.lower() == title), None)
    if candidate is None:
        return {"verified": False, "reason": "Candidate not found in the checked-in fixture"}
    decision = assess_candidate(candidate)
    return {
        "verified": bool(candidate.escrowed and candidate.sponsor_verified),
        "title": candidate.title,
        "escrowed": candidate.escrowed,
        "sponsor_verified": candidate.sponsor_verified,
        "payout_rail_ready": candidate.payout_rail_ready,
        "verdict": decision.verdict,
        "disclosure": "Advertised payout is not treated as earned income.",
    }


def _submission_status(arguments: dict[str, Any]) -> dict[str, Any]:
    requested = str(arguments.get("track") or "Alexa+").strip()
    return {
        "track": requested,
        "project": "RewardRadar",
        "state": "prototype",
        "registration": "owner confirmation required",
        "submission": "not submitted",
        "payout": "not awarded",
        "disclosure": "This endpoint never claims a prize or payment.",
    }


def _bounded_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    """Parse an untrusted voice argument without allowing unbounded work."""

    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    if parsed != parsed:  # NaN
        parsed = default
    return round(min(max(parsed, minimum), maximum), 2)


def _decision_card(decision: Any) -> dict[str, Any]:
    """Return public, inspectable evidence for one ranked fixture row."""

    candidate = decision.candidate
    gaps: list[str] = []
    if not candidate.sponsor_verified:
        gaps.append("Independently verify the sponsor before starting")
    if not candidate.acceptance_clear:
        gaps.append("Confirm acceptance criteria against the canonical source")
    if not candidate.payout_rail_ready:
        gaps.append("Confirm the accepted payout rail before starting")
    if candidate.locked:
        gaps.append("The fixture records a locked source")
    if candidate.status.lower() != "open":
        gaps.append(f"The fixture records source status={candidate.status}")
    return {
        "title": candidate.title,
        "source": candidate.source,
        "url": candidate.url,
        "advertised_payout_usd": candidate.payout_usd,
        "estimated_hours": candidate.estimated_hours,
        "payment_probability": decision.payment_probability,
        "probability_basis": candidate.probability_basis
        or "Explicit fixture scenario input; not an observed win rate",
        "expected_value_usd": decision.expected_value_usd,
        "expected_hourly_usd": decision.expected_hourly_usd,
        "verdict": decision.verdict,
        "reasons": decision.reasons,
        "verification_gaps": gaps,
    }


def _next_steps(recommendation: dict[str, Any] | None) -> list[str]:
    if recommendation is None:
        return [
            "Review the canonical source manually",
            "Do not spend time or money on an unmatched fixture row",
        ]
    return [
        "Open the canonical source and verify it is still open",
        "Confirm acceptance criteria and payout rail before starting",
        "Prepare a local draft and tests before any owner-approved submission",
    ]


def _casefile_metadata(case_id: str, ttl_seconds: int, fixture_digest: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "state": "open",
        "fixture_digest_sha256": fixture_digest,
        "capture": "checked-in data/demo_candidates.json",
        "expires_in_seconds": ttl_seconds,
        "persistence": "memory-only within this local MCP server process; resumable after reconnect or initialize",
    }


def _plan_pursuit(arguments: dict[str, Any], case_store: CaseStore = DEFAULT_CASE_STORE) -> dict[str, Any]:
    """Open a read-only, resumable evidence case from fixture evidence.

    The stored case intentionally omits the raw user query and retains only
    public fixture evidence, numeric constraints, and explicit verification
    gates. It never submits, contacts, spends, or configures a payout.
    """

    query = str(arguments.get("query") or "").strip().lower()
    max_hours = _bounded_float(arguments.get("max_hours", 8), 8, 0.5, 168)
    minimum_payout = _bounded_float(arguments.get("minimum_payout_usd", 50), 50, 0, 1_000_000)
    decisions = rank_candidates(_matching_candidates(query))
    eligible = [
        decision
        for decision in decisions
        if decision.candidate.payout_usd >= minimum_payout
        and decision.candidate.estimated_hours <= max_hours
        and decision.verdict in {"pursue", "watch"}
    ]
    recommendation = _decision_card(eligible[0]) if eligible else None
    alternatives = [
        _decision_card(decision)
        for decision in decisions
        if recommendation is None or decision.candidate.title != recommendation["title"]
    ][:3]
    next_steps = _next_steps(recommendation)
    fixture_digest = _fixture_digest()
    case_id, ttl_seconds = case_store.create(
        {
            "fixture_digest_sha256": fixture_digest,
            "capture": "checked-in data/demo_candidates.json",
            "constraints": {"max_hours": max_hours, "minimum_payout_usd": minimum_payout},
            "recommendation": recommendation,
            "alternatives": alternatives,
            "next_steps": next_steps,
            "safety": {"external_action": "owner_confirmation_required", "payout_guaranteed": False},
            "disclosure": "Fixture replay; no live source, submission, or payment action was performed.",
        }
    )
    if recommendation is None:
        voice_summary = "No checked-in opportunity meets those limits."
    else:
        voice_summary = (
            f"{recommendation['title']} is the best fixture match at an advertised "
            f"${recommendation['advertised_payout_usd']:,.2f}. Under the stated "
            f"planning scenario, its illustrative value is "
            f"${recommendation['expected_value_usd']:,.2f}; this is not an empirical "
            "win-rate estimate, forecast, or guaranteed income."
        )
    return {
        "mode": "fixture",
        "query": query,
        "constraints": {"max_hours": max_hours, "minimum_payout_usd": minimum_payout},
        "recommendation": recommendation,
        "voice_summary": voice_summary,
        "next_steps": next_steps,
        "casefile": _casefile_metadata(case_id, ttl_seconds, fixture_digest),
        "safety": {"external_action": "owner_confirmation_required", "payout_guaranteed": False},
        "disclosure": "Fixture replay; no live source, submission, or payment action was performed.",
    }


def _review_pursuit_case(arguments: dict[str, Any], case_store: CaseStore = DEFAULT_CASE_STORE) -> dict[str, Any]:
    """Resume a local casefile without refreshing sources or taking action."""

    case_id = arguments.get("case_id")
    focus = str(arguments.get("focus") or "overview").strip().lower()
    allowed_focuses = {"overview", "comparison", "evidence", "next_steps"}
    if focus not in allowed_focuses:
        return {
            "case_found": False,
            "reason": "focus must be overview, comparison, evidence, or next_steps",
            "safety": {"external_action": "owner_confirmation_required", "payout_guaranteed": False},
        }
    case = case_store.get(case_id)
    if case is None:
        return {
            "case_found": False,
            "state": "expired_or_unknown",
            "reason": "Case ids are opaque, memory-only, and expire automatically.",
            "safety": {"external_action": "owner_confirmation_required", "payout_guaranteed": False},
            "disclosure": "No source was refreshed and no external action was performed.",
        }
    if case["fixture_digest_sha256"] != _fixture_digest():
        return {
            "case_found": False,
            "state": "fixture_changed",
            "reason": "The checked-in fixture changed after this case was captured; start a new case.",
            "safety": {"external_action": "owner_confirmation_required", "payout_guaranteed": False},
            "disclosure": "Stale fixture evidence is not reused as a current recommendation.",
        }

    evidence_card: dict[str, Any] = {
        "recommendation": case["recommendation"],
        "fixture_digest_sha256": case["fixture_digest_sha256"],
        "capture": case["capture"],
    }
    if focus in {"overview", "comparison"}:
        evidence_card["alternatives"] = case["alternatives"]
    if focus in {"overview", "evidence"}:
        evidence_card["verification_gaps"] = (
            case["recommendation"]["verification_gaps"] if case["recommendation"] else []
        )
    if focus in {"overview", "next_steps"}:
        evidence_card["next_steps"] = case["next_steps"]
    return {
        "case_found": True,
        "state": "open",
        "focus": focus,
        "constraints": case["constraints"],
        "evidence_card": evidence_card,
        "safety": case["safety"],
        "disclosure": case["disclosure"],
    }


_REQUEST_NUMBER = r"\d+(?:,\d{3})*(?:\.\d{1,2})?"
_EXTERNAL_ACTION_REQUEST = re.compile(
    r"\b(?:submit(?:ted|ting)?|apply|send|email|message|contact|call|pay(?:ment)?|"
    r"transfer|withdraw|claim|register|sign[\s-]*up|log[\s-]*in|upload|publish|"
    r"buy|purchase|kyc|wallet|stripe)\b",
    re.IGNORECASE,
)


def _request_constraints(request: str) -> tuple[float, float, dict[str, bool]]:
    """Extract only explicit dollar-floor and effort constraints from a request."""

    payout_match = re.search(rf"\$\s*({_REQUEST_NUMBER})", request)
    if payout_match is None:
        payout_match = re.search(
            rf"\b(?:at least|over|above|more than|minimum(?: payout)?(?: of)?)\s+\$?({_REQUEST_NUMBER})\b",
            request,
            re.IGNORECASE,
        )
    hours_match = re.search(
        rf"\b(?:within|under|less than|in|for|at most|max(?:imum)?(?: of)?|finish in|fit in)\s+({_REQUEST_NUMBER})\s*(?:hours?|hrs?|h)\b",
        request,
        re.IGNORECASE,
    )

    minimum_payout = float(payout_match.group(1).replace(",", "")) if payout_match else 50.0
    max_hours = float(hours_match.group(1).replace(",", "")) if hours_match else 8.0
    return (
        _bounded_float(minimum_payout, 50, 0, 1_000_000),
        _bounded_float(max_hours, 8, 0.5, 168),
        {"minimum_payout_usd": payout_match is not None, "max_hours": hours_match is not None},
    )


def _respond_to_request(arguments: dict[str, Any], case_store: CaseStore = DEFAULT_CASE_STORE) -> dict[str, Any]:
    """Route a short natural-language prompt to a bounded, read-only fixture operation.

    Prompt text is parsed in process and is never persisted in the case store.
    The only supported operations are a fixture-backed plan, a read-only status
    summary, or a review of the caller-provided opaque case id.
    """

    request = arguments.get("request")
    if not isinstance(request, str) or not request.strip():
        return {
            "request_supported": False,
            "reason": "Enter a short request, such as a payout floor and maximum number of hours.",
            "safety": {"external_action": "disabled", "payout_guaranteed": False},
        }
    request = request.strip()
    if len(request) > 280:
        return {
            "request_supported": False,
            "reason": "Requests are limited to 280 characters; shorten it and try again.",
            "safety": {"external_action": "disabled", "payout_guaranteed": False},
        }

    normalized = request.lower()
    if re.search(r"\b(?:submitted|submission status|registration status|did i enter)\b", normalized):
        status = _submission_status({"track": "Alexa+"})
        status.update(
            {
                "intent": "submission_status",
                "request_text_retained": False,
                "voice_summary": "RewardRadar is a prototype; its registration and submission are not verified, and no payout has been awarded.",
            }
        )
        return status

    if _EXTERNAL_ACTION_REQUEST.search(normalized):
        return {
            "request_supported": False,
            "intent": "external_action_unavailable",
            "voice_summary": "This local demo is read-only. It cannot submit, contact anyone, create accounts, publish, pay, or configure a wallet.",
            "safety": {"external_action": "disabled", "payout_guaranteed": False},
            "disclosure": "No tool, account, network, or external action was performed.",
        }

    case_id = arguments.get("case_id")
    if isinstance(case_id, str) and case_id:
        if re.search(r"\b(fund|funded|funding|escrow|sponsor verified|payout rail)\b", normalized):
            case = case_store.get(case_id)
            if case is None:
                return {
                    "case_found": False,
                    "state": "expired_or_unknown",
                    "intent": "verify_funding",
                    "voice_summary": "I could not verify funding because the saved evidence case is missing or expired. Start a new fixture review first.",
                    "safety": {"external_action": "disabled", "payout_guaranteed": False},
                }
            if case["fixture_digest_sha256"] != _fixture_digest():
                return {
                    "case_found": False,
                    "state": "fixture_changed",
                    "intent": "verify_funding",
                    "voice_summary": "I did not reuse the saved case because its fixture evidence has changed. Start a new review first.",
                    "safety": {"external_action": "disabled", "payout_guaranteed": False},
                }
            recommendation = case.get("recommendation")
            if not recommendation:
                return {
                    "case_found": True,
                    "intent": "verify_funding",
                    "verified": False,
                    "reason": "The saved case has no recommended fixture candidate to check.",
                    "safety": {"external_action": "disabled", "payout_guaranteed": False},
                }
            funding = _verify_funding({"title": recommendation["title"]})
            escrow = "verified" if funding.get("escrowed") else "not verified"
            sponsor = "verified" if funding.get("sponsor_verified") else "not verified"
            rail = "ready" if funding.get("payout_rail_ready") else "not verified"
            funding.update(
                {
                    "case_found": True,
                    "intent": "verify_funding",
                    "request_text_retained": False,
                    "voice_summary": (
                        f"Funding signals for {funding['title']}: escrow {escrow}, sponsor {sponsor}, "
                        f"payout rail {rail}. This does not guarantee payment."
                    ),
                }
            )
            return funding

        if re.search(r"\b(compare|comparison|alternatives|other options)\b", normalized):
            focus = "comparison"
        elif re.search(r"\b(evidence|source|proof|verify|verified|funded|escrow|gap|gaps|why)\b", normalized):
            focus = "evidence"
        elif re.search(r"\b(next|steps|should i do|what now)\b", normalized):
            focus = "next_steps"
        else:
            focus = "overview"
        review = _review_pursuit_case({"case_id": case_id, "focus": focus}, case_store)
        review.update(
            {
                "intent": "review_pursuit_case",
                "request_text_retained": False,
                "voice_summary": (
                    "The saved fixture case could not be reopened; it may have expired or the fixture changed."
                    if not review.get("case_found")
                    else f"Here is the saved case {focus.replace('_', ' ')}. Its source is a checked-in fixture, not a live opportunity feed."
                ),
            }
        )
        return review

    minimum_payout, max_hours, explicit = _request_constraints(request)
    plan = _plan_pursuit(
        {"minimum_payout_usd": minimum_payout, "max_hours": max_hours},
        case_store,
    )
    plan["intent"] = "plan_pursuit"
    plan["request_text_retained"] = False
    plan["interpreted_constraints"] = {
        **plan["constraints"],
        "explicitly_requested": explicit,
    }
    plan["voice_summary"] = (
        f"I used a minimum advertised payout of ${minimum_payout:,.2f} and a maximum of {max_hours:g} hours. "
        f"{plan['voice_summary']}"
    )
    return plan


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "search_rewards",
        "description": "Search the transparent RewardRadar fixture and rank opportunities by payment-adjusted hourly value.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional title or source filter."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 20},
            },
        },
    },
    {
        "name": "verify_funding",
        "description": "Check escrow and sponsor evidence for one fixture candidate without claiming that a payout is guaranteed.",
        "inputSchema": {
            "type": "object",
            "required": ["title"],
            "properties": {"title": {"type": "string"}},
        },
    },
    {
        "name": "summarize_submission_status",
        "description": "Return an honest, non-financial status summary for the Alexa+ prototype.",
        "inputSchema": {
            "type": "object",
            "properties": {"track": {"type": "string"}},
        },
    },
    {
        "name": "plan_pursuit",
        "description": "Open a read-only, fixture-backed evidence case under payout and time limits; never submits or spends.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional title or source filter."},
                "max_hours": {"type": "number", "minimum": 0.5, "maximum": 168},
                "minimum_payout_usd": {"type": "number", "minimum": 0},
            },
        },
    },
    {
        "name": "review_pursuit_case",
        "description": "Resume one opaque local evidence case after reconnect; never refreshes sources or takes an external action.",
        "inputSchema": {
            "type": "object",
            "required": ["case_id"],
            "properties": {
                "case_id": {"type": "string", "minLength": 32, "maxLength": 32},
                "focus": {
                    "type": "string",
                    "enum": ["overview", "comparison", "evidence", "next_steps"],
                },
            },
        },
    },
    {
        "name": "respond_to_request",
        "description": "Interpret a short natural-language request locally and route it only to a fixture-backed plan, submission-status summary, or review of a caller-provided case id. It never performs external actions and does not retain prompt text.",
        "inputSchema": {
            "type": "object",
            "required": ["request"],
            "properties": {
                "request": {"type": "string", "minLength": 1, "maxLength": 280},
                "case_id": {"type": "string", "minLength": 32, "maxLength": 32},
            },
        },
    },
]


def handle_rpc(
    message: dict[str, Any],
    case_store: CaseStore = DEFAULT_CASE_STORE,
) -> dict[str, Any] | None:
    """Handle one JSON-RPC request and return its response, if applicable."""

    method = message.get("method")
    request_id = message.get("id")
    if request_id is None and method == "notifications/initialized":
        return None
    if not isinstance(method, str):
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32600, "message": "Invalid Request"}}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": SERVER_INFO,
                "instructions": "RewardRadar verifies evidence before a contributor spends time.",
            },
        }
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOL_DEFINITIONS}}
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        arguments = params.get("arguments") or {}
        handlers = {
            "search_rewards": _search_rewards,
            "verify_funding": _verify_funding,
            "summarize_submission_status": _submission_status,
            "plan_pursuit": lambda arguments: _plan_pursuit(arguments, case_store),
            "review_pursuit_case": lambda arguments: _review_pursuit_case(arguments, case_store),
            "respond_to_request": lambda arguments: _respond_to_request(arguments, case_store),
        }
        handler = handlers.get(name)
        if handler is None:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Unknown tool: {name}"}}
        try:
            return {"jsonrpc": "2.0", "id": request_id, "result": _result_text(handler(arguments))}
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32603, "message": f"Tool failed: {type(exc).__name__}"}}
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


class MCPHandler(BaseHTTPRequestHandler):
    # Keep the HTTP response identity synchronized with the MCP initialize
    # identity so a local judge does not observe two incompatible versions.
    server_version = f"RewardRadarMCP/{SERVER_INFO['version']}"
    allowed_origins = {
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    }

    def _reject_invalid_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is not None and origin not in self.allowed_origins:
            if self.command == "POST":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = -1
                if 0 <= length <= 1024 * 1024:
                    self.rfile.read(length)
                else:
                    self.close_connection = True
            self._send_json({"error": "Origin is not allowed"}, HTTPStatus.FORBIDDEN)
            return True
        return False

    def _cors_origin(self) -> str | None:
        origin = self.headers.get("Origin")
        return origin if origin in self.allowed_origins else None

    def _send_json(
        self,
        payload: dict[str, Any],
        status: int = HTTPStatus.OK,
        *,
        session_id: str | None = None,
    ) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if session_id is not None:
            self.send_header("Mcp-Session-Id", session_id)
        origin = self._cors_origin()
        if origin:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id, Server")
            self.send_header("Vary", "Origin")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self._send_json({"error": "MCP endpoint is /mcp"}, HTTPStatus.NOT_FOUND)
            return
        origin = self._cors_origin()
        if origin is None:
            self._send_json({"error": "Origin is not allowed"}, HTTPStatus.FORBIDDEN)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type, MCP-Session-Id, MCP-Protocol-Version")
        self.send_header("Access-Control-Max-Age", "300")
        self.send_header("Vary", "Origin")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self._reject_invalid_origin():
            return
        if self.path == "/mcp":
            self._send_json({"error": "This MCP server does not offer an SSE stream"}, HTTPStatus.METHOD_NOT_ALLOWED)
            return
        if self.path != "/health":
            self._send_json({"error": "Use POST /mcp"}, HTTPStatus.NOT_FOUND)
            return
        self._send_json({"ok": True, "server": SERVER_INFO, "mode": "fixture"})

    def do_POST(self) -> None:  # noqa: N802
        if self._reject_invalid_origin():
            return
        if self.path != "/mcp":
            self._send_json({"error": "MCP endpoint is /mcp"}, HTTPStatus.NOT_FOUND)
            return
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            self._send_json({"error": "Content-Type must be application/json"}, HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
            return
        accepted_types = {
            part.split(";", 1)[0].strip().lower()
            for part in self.headers.get("Accept", "").split(",")
        }
        if not {"application/json", "text/event-stream"}.issubset(accepted_types):
            self._send_json(
                {"error": "Accept must include application/json and text/event-stream"},
                HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0:
            self._send_json({"error": "A valid Content-Length is required"}, HTTPStatus.BAD_REQUEST)
            return
        if length > 1024 * 1024:
            self.close_connection = True
            self._send_json({"error": "Request body exceeds 1 MiB"}, HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return
        try:
            message = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            self._send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}, HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(message, dict):
            self._send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}, HTTPStatus.BAD_REQUEST)
            return
        if message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
            self._send_json({"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32600, "message": "Invalid Request"}}, HTTPStatus.BAD_REQUEST)
            return

        method = message["method"]
        supplied_session = self.headers.get("Mcp-Session-Id")
        if method == "initialize":
            if message.get("id") is None or supplied_session is not None:
                self._send_json({"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32600, "message": "Initialize must be a request without an existing session"}}, HTTPStatus.BAD_REQUEST)
                return
            params = message.get("params")
            if not isinstance(params, dict) or not isinstance(params.get("protocolVersion"), str):
                self._send_json({"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32602, "message": "Initialize requires params.protocolVersion"}}, HTTPStatus.BAD_REQUEST)
                return
            session_id = self.server.create_session()
            response = handle_rpc(message, self.server.case_store)
            self._send_json(response, session_id=session_id)
            return

        if not supplied_session:
            self._send_json({"error": "MCP-Session-Id is required after initialization"}, HTTPStatus.BAD_REQUEST)
            return
        session = self.server.get_session(supplied_session)
        if session is None:
            self._send_json({"error": "MCP session was not found or has expired"}, HTTPStatus.NOT_FOUND)
            return
        protocol_header = self.headers.get("MCP-Protocol-Version")
        if protocol_header != session["protocol_version"]:
            self._send_json({"error": "MCP-Protocol-Version is missing or unsupported"}, HTTPStatus.BAD_REQUEST)
            return
        if method == "notifications/initialized" and "id" not in message:
            if self.server.update_session(supplied_session, initialized=True) is None:
                self._send_json({"error": "MCP session was not found or has expired"}, HTTPStatus.NOT_FOUND)
                return
            self.send_response(HTTPStatus.ACCEPTED)
            origin = self._cors_origin()
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id, Server")
                self.send_header("Vary", "Origin")
            self.end_headers()
            return
        session = self.server.update_session(supplied_session)
        if session is None:
            self._send_json({"error": "MCP session was not found or has expired"}, HTTPStatus.NOT_FOUND)
            return
        if not session["initialized"]:
            self._send_json({"error": "notifications/initialized must be received before requests"}, HTTPStatus.BAD_REQUEST)
            return
        if "id" not in message:
            self.send_response(HTTPStatus.ACCEPTED)
            origin = self._cors_origin()
            if origin:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id, Server")
                self.send_header("Vary", "Origin")
            self.end_headers()
            return
        response = handle_rpc(message, self.server.case_store)
        self._send_json(response)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[mcp] {format % args}")


class MCPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    session_ttl_seconds = 30 * 60
    max_sessions = 128

    def __init__(self, address: tuple[str, int]):
        super().__init__(address, MCPHandler)
        self.case_store = CaseStore()
        self._sessions: dict[str, dict[str, Any]] = {}
        self._sessions_lock = threading.RLock()

    def create_session(self) -> str:
        now = time.monotonic()
        with self._sessions_lock:
            self._prune_sessions(now)
            while len(self._sessions) >= self.max_sessions:
                oldest = min(self._sessions, key=lambda key: self._sessions[key]["last_seen"])
                del self._sessions[oldest]
            session_id = secrets.token_urlsafe(32)
            self._sessions[session_id] = {
                "protocol_version": PROTOCOL_VERSION,
                "initialized": False,
                "last_seen": now,
            }
            return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        now = time.monotonic()
        with self._sessions_lock:
            self._prune_sessions(now)
            session = self._sessions.get(session_id)
            return dict(session) if session is not None else None

    def update_session(
        self,
        session_id: str,
        *,
        initialized: bool = False,
    ) -> dict[str, Any] | None:
        now = time.monotonic()
        with self._sessions_lock:
            self._prune_sessions(now)
            session = self._sessions.get(session_id)
            if session is not None:
                session["last_seen"] = now
                if initialized:
                    session["initialized"] = True
                return dict(session)
            return None

    def _prune_sessions(self, now: float) -> None:
        for session_id, session in list(self._sessions.items()):
            if now - session["last_seen"] >= self.session_ttl_seconds:
                del self._sessions[session_id]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run RewardRadar's Alexa+ MCP prototype.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)
    server = MCPServer((args.host, args.port))
    print(f"RewardRadar Alexa+ MCP prototype listening on http://{args.host}:{args.port}/mcp")
    print("Mode: checked-in fixture; no credentials or payout actions are enabled.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
