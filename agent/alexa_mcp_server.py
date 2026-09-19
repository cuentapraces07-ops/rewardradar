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
import json
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .core import Candidate, assess_candidate, rank_candidates


# Keep this endpoint dependency-free so judges can reproduce the MCP protocol
# without installing the optional Strands runtime first.
DEMO_FIXTURE = Path(__file__).parents[1] / "data" / "demo_candidates.json"


PROTOCOL_VERSION = "2025-11-25"
SERVER_INFO = {"name": "rewardradar-alexa-plus", "version": "0.2.0"}


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


def _plan_pursuit(arguments: dict[str, Any]) -> dict[str, Any]:
    """Produce a read-only, voice-ready next-step brief from fixture evidence.

    This tool intentionally plans but never submits, contacts, spends, or
    configures a payout destination. The explicit owner gate is part of the
    response so a voice client cannot turn a recommendation into an external
    action by implication.
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
    if not eligible:
        return {
            "mode": "fixture",
            "query": query,
            "constraints": {"max_hours": max_hours, "minimum_payout_usd": minimum_payout},
            "recommendation": None,
            "voice_summary": "No checked-in opportunity meets those limits.",
            "next_steps": ["Review the canonical source manually", "Do not spend time or money on an unmatched row"],
            "safety": {"external_action": "owner_confirmation_required", "payout_guaranteed": False},
            "disclosure": "Fixture replay; no live source, submission, or payment action was performed.",
        }

    decision = eligible[0]
    candidate = decision.candidate
    return {
        "mode": "fixture",
        "query": query,
        "constraints": {"max_hours": max_hours, "minimum_payout_usd": minimum_payout},
        "recommendation": {
            "title": candidate.title,
            "source": candidate.source,
            "url": candidate.url,
            "advertised_payout_usd": candidate.payout_usd,
            "estimated_hours": candidate.estimated_hours,
            "payment_probability": decision.payment_probability,
            "expected_value_usd": decision.expected_value_usd,
            "expected_hourly_usd": decision.expected_hourly_usd,
            "verdict": decision.verdict,
            "reasons": decision.reasons,
        },
        "voice_summary": (
            f"{candidate.title} is the best fixture match at an advertised "
            f"${candidate.payout_usd:,.2f}; expected value is "
            f"${decision.expected_value_usd:,.2f}, not guaranteed income."
        ),
        "next_steps": [
            "Open the canonical source and verify it is still open",
            "Confirm acceptance criteria and payout rail before starting",
            "Prepare a local draft and tests before any owner-approved submission",
        ],
        "safety": {"external_action": "owner_confirmation_required", "payout_guaranteed": False},
        "disclosure": "Fixture replay; no live source, submission, or payment action was performed.",
    }


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
        "description": "Build a read-only, voice-ready next-step brief under payout and time limits; never submits or spends.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Optional title or source filter."},
                "max_hours": {"type": "number", "minimum": 0.5, "maximum": 168},
                "minimum_payout_usd": {"type": "number", "minimum": 0},
            },
        },
    },
]


def handle_rpc(message: dict[str, Any]) -> dict[str, Any] | None:
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
            "plan_pursuit": _plan_pursuit,
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
    server_version = "RewardRadarMCP/0.1"

    def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Mcp-Session-Id", self.server.session_id)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/health":
            self._send_json({"error": "Use POST /mcp"}, HTTPStatus.NOT_FOUND)
            return
        self._send_json({"ok": True, "server": SERVER_INFO, "mode": "fixture"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/mcp":
            self._send_json({"error": "MCP endpoint is /mcp"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            message = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            self._send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}, HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(message, dict):
            self._send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}, HTTPStatus.BAD_REQUEST)
            return
        response = handle_rpc(message)
        if response is None:
            self.send_response(HTTPStatus.ACCEPTED)
            self.send_header("Mcp-Session-Id", self.server.session_id)
            self.end_headers()
            return
        self._send_json(response)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[mcp] {format % args}")


class MCPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int]):
        super().__init__(address, MCPHandler)
        self.session_id = uuid.uuid4().hex


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
