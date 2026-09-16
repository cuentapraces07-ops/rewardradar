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
import os
import secrets
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .core import Candidate, assess_candidate, rank_candidates


# Keep this endpoint dependency-free so judges can reproduce the MCP protocol
# without installing the optional Strands runtime first.
DEMO_FIXTURE = Path(__file__).parents[1] / "data" / "demo_candidates.json"


PROTOCOL_VERSION = "2025-11-25"
SERVER_INFO = {"name": "rewardradar-alexa-plus", "version": "0.1.0"}
MAX_REQUEST_BYTES = 64 * 1024
MAX_SESSIONS = 128
SESSION_TTL_SECONDS = 60 * 60
DEFAULT_ALLOWED_ORIGINS = frozenset(
    {"http://localhost:5173", "http://127.0.0.1:5173"}
)


def _normalize_origin(value: str) -> str:
    """Validate and normalize one exact browser origin (not a URL prefix)."""

    if not isinstance(value, str) or not value:
        raise ValueError("allowed origins must be non-empty HTTP(S) origins")
    parsed = urlsplit(value)
    if (
        parsed.scheme.lower() not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"invalid HTTP(S) origin: {value!r}")
    try:
        port = parsed.port
    except ValueError as error:
        raise ValueError(f"invalid HTTP(S) origin: {value!r}") from error
    if port == 0 or parsed.netloc.endswith(":"):
        raise ValueError(f"invalid HTTP(S) origin: {value!r}")
    scheme = parsed.scheme.lower()
    host = parsed.hostname.lower()
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    default_port = 80 if scheme == "http" else 443
    suffix = f":{port}" if port is not None and port != default_port else ""
    return f"{scheme}://{host}{suffix}"


def _allowed_origins(values: list[str] | None = None) -> frozenset[str]:
    if values is not None:
        candidates = values
    else:
        configured = os.environ.get("REWARDRADAR_ALLOWED_ORIGINS", "")
        candidates = [item.strip() for item in configured.split(",") if item.strip()]
        if not candidates:
            candidates = sorted(DEFAULT_ALLOWED_ORIGINS)
    return frozenset(_normalize_origin(item) for item in candidates)


def _fixture_candidates() -> list[Candidate]:
    payload = json.loads(DEMO_FIXTURE.read_text(encoding="utf-8"))
    return [Candidate(**item) for item in payload]


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
    candidates = _fixture_candidates()
    if query:
        candidates = [
            candidate
            for candidate in candidates
            if query in f"{candidate.title} {candidate.source}".lower()
        ]
    decisions = rank_candidates(candidates)[:limit]
    return {
        "mode": "fixture",
        "data_as_of": "2026-09-10",
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
        "source_url": candidate.url,
        "status": candidate.status,
        "data_as_of": "2026-09-10",
        "escrowed": candidate.escrowed,
        "sponsor_verified": candidate.sponsor_verified,
        "acceptance_clear": candidate.acceptance_clear,
        "payout_rail_ready": candidate.payout_rail_ready,
        "verdict": decision.verdict,
        "reasons": decision.reasons,
        "disclosure": "Advertised payout is not treated as earned income.",
    }


def _submission_status(arguments: dict[str, Any]) -> dict[str, Any]:
    requested = str(arguments.get("track") or "Alexa+").strip()
    if requested.casefold() not in {"alexa+", "alexa", "build, ship, shape: amazon developer hackathon"}:
        return {
            "track": requested,
            "project": "RewardRadar",
            "submission": "not confirmed for this track",
            "award": "not awarded",
            "payment": "not received",
            "disclosure": "This endpoint reports only the Alexa+ Devpost entry captured below.",
        }
    return {
        "track": "Alexa+",
        "project": "RewardRadar: Alexa+ Opportunity Scout",
        "submission": "submitted",
        "submitted_on": "2026-09-14",
        "submission_url": "https://devpost.com/software/rewardradar-alexa-opportunity-scout",
        "award": "not announced",
        "payment": "not received",
        "as_of": "2026-09-14",
        "disclosure": "A submitted entry is not an award; no prize or payment is claimed.",
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
]


def handle_rpc(message: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one JSON-RPC request and return its response, if applicable."""

    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    method = message.get("method")
    request_id = message.get("id")
    has_id = "id" in message
    if has_id and (isinstance(request_id, bool) or not isinstance(request_id, (str, int))):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    if not isinstance(method, str):
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32600, "message": "Invalid Request"}}
    if not has_id:
        if method.startswith("notifications/"):
            return None
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}
    params = message.get("params", {})
    if not isinstance(params, dict):
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Invalid params"}}

    if method == "initialize":
        client_info = params.get("clientInfo")
        if (
            not isinstance(params.get("protocolVersion"), str)
            or not isinstance(params.get("capabilities"), dict)
            or not isinstance(client_info, dict)
            or not isinstance(client_info.get("name"), str)
            or not isinstance(client_info.get("version"), str)
        ):
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Invalid initialize params"}}
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
        if params and not isinstance(params.get("cursor", ""), str):
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Invalid params"}}
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOL_DEFINITIONS}}
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str) or not isinstance(arguments, dict):
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": "Invalid params"}}
        handlers = {
            "search_rewards": _search_rewards,
            "verify_funding": _verify_funding,
            "summarize_submission_status": _submission_status,
        }
        handler = handlers.get(name)
        if handler is None:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32602, "message": f"Unknown tool: {name}"}}
        try:
            return {"jsonrpc": "2.0", "id": request_id, "result": _result_text(handler(arguments))}
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": f"Tool failed: {type(exc).__name__}"}],
                    "isError": True,
                },
            }
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


class MCPHandler(BaseHTTPRequestHandler):
    server_version = "RewardRadarMCP/0.1"

    def _check_origin(self) -> bool:
        self._cors_origin: str | None = None
        origin = self.headers.get("Origin")
        if origin is None:
            return True
        try:
            normalized = _normalize_origin(origin)
        except ValueError:
            normalized = ""
        if normalized not in self.server.allowed_origins:
            self._send_empty(HTTPStatus.FORBIDDEN)
            return False
        self._cors_origin = normalized
        return True

    def _add_cors_headers(self) -> None:
        if self._cors_origin is None:
            return
        self.send_header("Access-Control-Allow-Origin", self._cors_origin)
        self.send_header("Access-Control-Expose-Headers", "Mcp-Session-Id")
        self.send_header("Vary", "Origin")

    def _send_empty(
        self,
        status: int,
        *,
        allow: str | None = None,
        session_id: str | None = None,
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self._add_cors_headers()
        if allow is not None:
            self.send_header("Allow", allow)
        if session_id is not None:
            self.send_header("Mcp-Session-Id", session_id)
        self.end_headers()

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
        self._add_cors_headers()
        if session_id is not None:
            self.send_header("Mcp-Session-Id", session_id)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        if not self._check_origin():
            return
        if self.path != "/mcp":
            self._send_empty(HTTPStatus.NOT_FOUND)
            return
        requested_method = self.headers.get("Access-Control-Request-Method", "POST").upper()
        if requested_method not in {"POST", "GET", "DELETE"}:
            self._send_empty(HTTPStatus.METHOD_NOT_ALLOWED)
            return
        allowed_headers = {"accept", "content-type", "mcp-protocol-version", "mcp-session-id"}
        requested_headers = {
            item.strip().lower()
            for item in self.headers.get("Access-Control-Request-Headers", "").split(",")
            if item.strip()
        }
        if not requested_headers.issubset(allowed_headers):
            self._send_empty(HTTPStatus.FORBIDDEN)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self._add_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "POST, GET, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Accept, Content-Type, MCP-Protocol-Version, MCP-Session-Id")
        self.send_header("Access-Control-Max-Age", "600")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _accepts(self, required_types: set[str]) -> bool:
        accepted: set[str] = set()
        for item in self.headers.get("Accept", "").split(","):
            media_type, *parameters = item.split(";")
            quality = 1.0
            for parameter in parameters:
                key, separator, value = parameter.strip().partition("=")
                if separator and key.lower() == "q":
                    try:
                        quality = float(value)
                    except ValueError:
                        quality = 0.0
            if quality > 0:
                accepted.add(media_type.strip().lower())
        return required_types.issubset(accepted)

    def _request_has_json_content(self) -> bool:
        return self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower() == "application/json"

    def _check_protocol_header(self, *, initialize: bool = False) -> bool:
        supplied = self.headers.get("MCP-Protocol-Version")
        if supplied == PROTOCOL_VERSION or (initialize and supplied is None):
            return True
        self._send_empty(HTTPStatus.BAD_REQUEST)
        return False

    def _require_session(self) -> tuple[str | None, bool | None]:
        session_id = self.headers.get("Mcp-Session-Id")
        if not session_id:
            self._send_empty(HTTPStatus.BAD_REQUEST)
            return None, None
        initialized = self.server.session_initialized(session_id)
        if initialized is None:
            self._send_empty(HTTPStatus.NOT_FOUND)
            return None, None
        return session_id, initialized

    def do_GET(self) -> None:  # noqa: N802
        if not self._check_origin():
            return
        if self.path == "/health":
            self._send_json({"ok": True, "server": SERVER_INFO, "mode": "fixture"})
            return
        if self.path == "/mcp":
            if not self._accepts({"text/event-stream"}):
                self._send_empty(HTTPStatus.NOT_ACCEPTABLE)
            else:
                self._send_empty(HTTPStatus.METHOD_NOT_ALLOWED, allow="POST, GET, OPTIONS")
            return
        self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._check_origin():
            return
        if self.path != "/mcp":
            self._send_empty(HTTPStatus.NOT_FOUND)
            return
        if not self._check_protocol_header():
            return
        session_id = self.headers.get("Mcp-Session-Id")
        if not session_id:
            self._send_empty(HTTPStatus.BAD_REQUEST)
            return
        if not self.server.delete_session(session_id):
            self._send_empty(HTTPStatus.NOT_FOUND)
            return
        self._send_empty(HTTPStatus.NO_CONTENT)

    def do_POST(self) -> None:  # noqa: N802
        if not self._check_origin():
            return
        if self.path != "/mcp":
            self._send_json({"error": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            length = 0
        if length <= 0:
            self._send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}, HTTPStatus.BAD_REQUEST)
            return
        if length > MAX_REQUEST_BYTES:
            self._send_empty(HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
            return
        try:
            raw_body = self.rfile.read(length)
            if len(raw_body) != length:
                raise json.JSONDecodeError("incomplete request body", "", len(raw_body))
        except json.JSONDecodeError:
            self._send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}, HTTPStatus.BAD_REQUEST)
            return
        if not self._accepts({"application/json", "text/event-stream"}):
            self._send_empty(HTTPStatus.NOT_ACCEPTABLE)
            return
        if not self._request_has_json_content():
            self._send_empty(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)
            return
        try:
            message = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}, HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            self._send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}, HTTPStatus.BAD_REQUEST)
            return

        method = message.get("method")
        if method == "initialize":
            if message.get("id") is None or not self._check_protocol_header(initialize=True):
                if message.get("id") is None:
                    self._send_json({"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}}, HTTPStatus.BAD_REQUEST)
                return
            if self.headers.get("Mcp-Session-Id") is not None:
                self._send_empty(HTTPStatus.BAD_REQUEST)
                return
            response = handle_rpc(message)
            if response is None or "error" in response:
                self._send_json(response or {"jsonrpc": "2.0", "id": message.get("id"), "error": {"code": -32600, "message": "Invalid Request"}})
                return
            try:
                session_id = self.server.create_session()
            except RuntimeError:
                self._send_empty(HTTPStatus.SERVICE_UNAVAILABLE)
                return
            self._send_json(response, session_id=session_id)
            return

        if not self._check_protocol_header():
            return
        session_id, initialized = self._require_session()
        if session_id is None:
            return
        if not initialized:
            if method == "notifications/initialized" and "id" not in message:
                self.server.mark_initialized(session_id)
                self._send_empty(HTTPStatus.ACCEPTED, session_id=session_id)
                return
            self._send_empty(HTTPStatus.BAD_REQUEST)
            return

        if method is None and ("result" in message or "error" in message):
            self._send_empty(HTTPStatus.ACCEPTED, session_id=session_id)
            return
        response = handle_rpc(message)
        if response is None:
            self._send_empty(HTTPStatus.ACCEPTED, session_id=session_id)
            return
        self._send_json(response, session_id=session_id)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[mcp] {format % args}")


class MCPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], allowed_origins: list[str] | None = None):
        super().__init__(address, MCPHandler)
        self.allowed_origins = _allowed_origins(allowed_origins)
        self._sessions: dict[str, tuple[float, bool]] = {}
        self._sessions_lock = threading.Lock()

    def _expire_sessions(self, now: float) -> None:
        expired = [
            session_id
            for session_id, (created_at, _) in self._sessions.items()
            if now - created_at >= SESSION_TTL_SECONDS
        ]
        for session_id in expired:
            del self._sessions[session_id]

    def create_session(self) -> str:
        now = time.monotonic()
        with self._sessions_lock:
            self._expire_sessions(now)
            if len(self._sessions) >= MAX_SESSIONS:
                raise RuntimeError("too many active MCP sessions")
            session_id = secrets.token_urlsafe(32)
            self._sessions[session_id] = (now, False)
            return session_id

    def session_initialized(self, session_id: str) -> bool | None:
        now = time.monotonic()
        with self._sessions_lock:
            self._expire_sessions(now)
            entry = self._sessions.get(session_id)
            if entry is None:
                return None
            created_at, initialized = entry
            self._sessions[session_id] = (created_at, initialized)
            return initialized

    def mark_initialized(self, session_id: str) -> None:
        with self._sessions_lock:
            entry = self._sessions.get(session_id)
            if entry is not None:
                self._sessions[session_id] = (entry[0], True)

    def delete_session(self, session_id: str) -> bool:
        with self._sessions_lock:
            return self._sessions.pop(session_id, None) is not None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run RewardRadar's Alexa+ MCP prototype.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument(
        "--allow-origin",
        action="append",
        default=None,
        help="Exact browser origin allowed by CORS; repeat to allow several. Defaults to localhost:5173.",
    )
    args = parser.parse_args(argv)
    server = MCPServer((args.host, args.port), allowed_origins=args.allow_origin)
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
