"""Offline HTTP contract tests for the Alexa+ MCP endpoint.

The Amazon rules require a working MCP server.  These tests bind only to an
ephemeral loopback port and never contact an external service.
"""

from __future__ import annotations

import http.client
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agent.alexa_mcp_server import MCPServer, PROTOCOL_VERSION, SERVER_INFO


class AlexaMCPHttpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = MCPServer(("127.0.0.1", 0))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def post(
        self,
        payload: dict,
        session_id: str | None = None,
        **overrides: str,
    ) -> tuple[int, dict | None, str | None]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if session_id:
            headers.update(
                {
                    "MCP-Protocol-Version": PROTOCOL_VERSION,
                    "Mcp-Session-Id": session_id,
                }
            )
        headers.update(overrides)
        request = Request(
            f"{self.base}/mcp",
            data=json.dumps(payload).encode(),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            body = response.read()
            return (
                response.status,
                json.loads(body) if body else None,
                response.headers.get("Mcp-Session-Id"),
            )

    def initialize(self) -> tuple[dict, str]:
        status, payload, session_id = self.post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            }
        )
        self.assertEqual(status, 200)
        self.assertIsNotNone(session_id)
        status, body, returned_session = self.post(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id
        )
        self.assertEqual(status, 202)
        self.assertIsNone(body)
        self.assertIsNone(returned_session)
        return payload, session_id

    def rpc(self, payload: dict, session_id: str | None = None) -> tuple[dict, str]:
        if payload.get("method") == "initialize":
            status, result, new_session_id = self.post(payload)
            self.assertEqual(status, 200)
            self.assertIsNotNone(new_session_id)
            return result, new_session_id
        if session_id is None:
            _, session_id = self.initialize()
        status, result, returned_session_id = self.post(payload, session_id)
        self.assertEqual(status, 200)
        self.assertIsNone(returned_session_id)
        return result, session_id

    def assert_http_error(self, status: int, request) -> None:
        with self.assertRaises(HTTPError) as raised:
            request()
        try:
            self.assertEqual(raised.exception.code, status)
        finally:
            raised.exception.close()

    def test_health_is_local_and_explicit(self):
        with urlopen(f"{self.base}/health", timeout=2) as response:
            payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["mode"], "fixture")
            self.assertNotIn("Mcp-Session-Id", response.headers)
            self.assertTrue(
                response.headers["Server"].startswith(
                    f"RewardRadarMCP/{SERVER_INFO['version']}"
                )
            )

    def test_streamable_http_initialize_and_tools_list(self):
        payload, session_id = self.initialize()
        self.assertEqual(payload["result"]["protocolVersion"], PROTOCOL_VERSION)
        self.assertGreaterEqual(len(session_id), 40)
        status, listed, returned_session = self.post(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, session_id
        )
        self.assertEqual(status, 200)
        self.assertIsNone(returned_session)
        names = [tool["name"] for tool in listed["result"]["tools"]]
        self.assertIn("plan_pursuit", names)

    def test_initialized_notification_is_accepted_without_body(self):
        status, _, session_id = self.post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": PROTOCOL_VERSION},
            }
        )
        self.assertEqual(status, 200)
        self.assertIsNotNone(session_id)
        request = Request(
            f"{self.base}/mcp",
            data=json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": PROTOCOL_VERSION,
                "Mcp-Session-Id": session_id,
            },
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            self.assertEqual(response.status, 202)
            self.assertNotIn("Mcp-Session-Id", response.headers)
            self.assertEqual(response.read(), b"")

    def test_browser_preflight_allows_only_the_local_demo_origins(self):
        allowed = Request(
            f"{self.base}/mcp",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,mcp-session-id,mcp-protocol-version",
            },
            method="OPTIONS",
        )
        with urlopen(allowed, timeout=2) as response:
            self.assertEqual(response.status, 204)
            self.assertEqual(response.headers["Access-Control-Allow-Origin"], "http://127.0.0.1:5173")
            self.assertIn("MCP-Session-Id", response.headers["Access-Control-Allow-Headers"])
            self.assertIn("MCP-Protocol-Version", response.headers["Access-Control-Allow-Headers"])

        blocked = Request(
            f"{self.base}/mcp",
            headers={"Origin": "https://attacker.example", "Access-Control-Request-Method": "POST"},
            method="OPTIONS",
        )
        self.assert_http_error(403, lambda: urlopen(blocked, timeout=2))

    def test_invalid_origin_is_rejected_on_mcp_post_and_health_get(self):
        request = Request(
            f"{self.base}/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(),
            headers={"Origin": "https://attacker.example", "Content-Type": "application/json"},
            method="POST",
        )
        self.assert_http_error(403, lambda: urlopen(request, timeout=2))

        self.assert_http_error(
            403,
            lambda: urlopen(
                Request(f"{self.base}/health", headers={"Origin": "https://attacker.example"}),
                timeout=2,
            ),
        )

    def test_mcp_get_returns_405_when_server_does_not_offer_sse(self):
        request = Request(
            f"{self.base}/mcp",
            headers={"Accept": "text/event-stream", "Origin": "http://localhost:5173"},
            method="GET",
        )
        self.assert_http_error(405, lambda: urlopen(request, timeout=2))

    def test_local_browser_origin_can_run_a_complete_read_only_mcp_tool_call(self):
        origin = "http://localhost:5173"

        def browser_post(payload: dict, session_id: str | None = None):
            headers = {
                "Origin": origin,
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
                "MCP-Protocol-Version": PROTOCOL_VERSION,
            }
            if session_id:
                headers["Mcp-Session-Id"] = session_id
            request = Request(
                f"{self.base}/mcp",
                data=json.dumps(payload).encode(),
                headers=headers,
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                self.assertEqual(response.headers["Access-Control-Allow-Origin"], origin)
                return response.status, response.headers.get("Mcp-Session-Id"), response.read()

        status, session_id, body = browser_post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "browser-test", "version": "1.0.0"},
                },
            }
        )
        self.assertEqual(status, 200)
        self.assertTrue(session_id)
        self.assertEqual(json.loads(body)["result"]["protocolVersion"], PROTOCOL_VERSION)

        status, _, body = browser_post(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id
        )
        self.assertEqual(status, 202)
        self.assertEqual(body, b"")

        status, _, body = browser_post(
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, session_id
        )
        self.assertEqual(status, 200)
        self.assertIn("search_rewards", [tool["name"] for tool in json.loads(body)["result"]["tools"]])

        status, _, body = browser_post(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "search_rewards", "arguments": {"query": "", "limit": 1}},
            },
            session_id,
        )
        result = json.loads(body)["result"]["structuredContent"]
        self.assertEqual(status, 200)
        self.assertEqual(result["mode"], "fixture")
        self.assertEqual(len(result["results"]), 1)

    def test_casefile_survives_a_new_http_initialize(self):
        _, first_session = self.initialize()
        planned, _ = self.rpc(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "plan_pursuit",
                    "arguments": {"minimum_payout_usd": 100, "max_hours": 40},
                },
            }, first_session
        )
        case_id = planned["result"]["structuredContent"]["casefile"]["case_id"]
        initialized, second_session = self.rpc(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "reconnect-test", "version": "1.0.0"},
                },
            }
        )
        self.assertNotEqual(first_session, second_session)
        self.assertEqual(initialized["result"]["protocolVersion"], PROTOCOL_VERSION)
        status, _, returned_session = self.post(
            {"jsonrpc": "2.0", "method": "notifications/initialized"}, second_session
        )
        self.assertEqual(status, 202)
        self.assertIsNone(returned_session)

        reviewed, third_session = self.rpc(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "review_pursuit_case",
                    "arguments": {"case_id": case_id, "focus": "evidence"},
                },
            }, second_session
        )
        value = reviewed["result"]["structuredContent"]
        self.assertEqual(third_session, second_session)
        self.assertTrue(value["case_found"])
        self.assertEqual(value["focus"], "evidence")
        self.assertIn("fixture_digest_sha256", value["evidence_card"])
        self.assertIn("verification_gaps", value["evidence_card"])

    def test_natural_request_and_followup_use_the_real_http_tool_boundary(self):
        _, session_id = self.initialize()
        planned, _ = self.rpc(
            {
                "jsonrpc": "2.0",
                "id": 30,
                "method": "tools/call",
                "params": {
                    "name": "respond_to_request",
                    "arguments": {"request": "Find an opportunity above $100 that fits in 40 hours."},
                },
            }, session_id
        )
        result = planned["result"]["structuredContent"]
        self.assertEqual(result["intent"], "plan_pursuit")
        case_id = result["casefile"]["case_id"]

        followed_up, _ = self.rpc(
            {
                "jsonrpc": "2.0",
                "id": 31,
                "method": "tools/call",
                "params": {
                    "name": "respond_to_request",
                    "arguments": {"request": "Compare the alternatives", "case_id": case_id},
                },
            }, session_id
        )
        value = followed_up["result"]["structuredContent"]
        self.assertTrue(value["case_found"])
        self.assertEqual(value["focus"], "comparison")
        self.assertIn("alternatives", value["evidence_card"])

    def test_sessions_are_unique_and_required_for_followup_requests(self):
        _, first_session = self.initialize()
        _, second_session = self.initialize()
        self.assertNotEqual(first_session, second_session)

        self.assert_http_error(
            400,
            lambda: self.post({"jsonrpc": "2.0", "id": 7, "method": "tools/list"}),
        )

        self.assert_http_error(
            400,
            lambda: self.post(
                {"jsonrpc": "2.0", "id": 8, "method": "tools/list"},
                first_session,
                **{"MCP-Protocol-Version": "2025-03-26"},
            ),
        )

    def test_requests_are_rejected_before_initialized_notification(self):
        status, _, session_id = self.post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": PROTOCOL_VERSION},
            }
        )
        self.assertEqual(status, 200)
        self.assert_http_error(
            400,
            lambda: self.post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, session_id),
        )

    def test_non_initialize_notifications_are_accepted_without_a_response_body(self):
        _, session_id = self.initialize()
        for notification in (
            {"jsonrpc": "2.0", "method": "notifications/cancelled", "params": {"requestId": 4}},
            {"jsonrpc": "2.0", "method": "tools/list"},
        ):
            status, body, returned_session = self.post(notification, session_id)
            self.assertEqual(status, 202)
            self.assertIsNone(body)
            self.assertIsNone(returned_session)

    def test_accept_content_type_and_expired_session_are_checked(self):
        initialize_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": PROTOCOL_VERSION},
        }
        self.assert_http_error(
            400,
            lambda: self.post(initialize_payload, **{"Accept": "application/json"}),
        )

        self.assert_http_error(
            415,
            lambda: self.post(initialize_payload, **{"Content-Type": "text/plain"}),
        )

        _, session_id = self.initialize()
        self.server._sessions[session_id]["last_seen"] -= self.server.session_ttl_seconds + 1
        self.assert_http_error(
            404,
            lambda: self.post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, session_id),
        )

    def test_oversized_request_body_is_rejected_before_reading_it(self):
        connection = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_address[1], timeout=2
        )
        try:
            connection.request(
                "POST",
                "/mcp",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "Content-Length": str(1024 * 1024 + 1),
                },
            )
            response = connection.getresponse()
            self.assertEqual(response.status, 413)
            self.assertIn("1 MiB", response.read().decode())
        finally:
            connection.close()


if __name__ == "__main__":
    unittest.main()
