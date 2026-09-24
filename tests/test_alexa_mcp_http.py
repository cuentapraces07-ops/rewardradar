"""Offline HTTP contract tests for the Alexa+ MCP endpoint.

The Amazon rules require a working MCP server.  These tests bind only to an
ephemeral loopback port and never contact an external service.
"""

from __future__ import annotations

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

    def rpc(self, payload: dict) -> tuple[dict, str]:
        request = Request(
            f"{self.base}/mcp",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "MCP-Protocol-Version": PROTOCOL_VERSION,
            },
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            return json.loads(response.read()), response.headers["Mcp-Session-Id"]

    def test_health_is_local_and_explicit(self):
        with urlopen(f"{self.base}/health", timeout=2) as response:
            payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["mode"], "fixture")
            self.assertEqual(response.headers["Mcp-Session-Id"], self.server.session_id)
            self.assertTrue(
                response.headers["Server"].startswith(
                    f"RewardRadarMCP/{SERVER_INFO['version']}"
                )
            )

    def test_streamable_http_initialize_and_tools_list(self):
        for request_id, method in ((1, "initialize"), (2, "tools/list")):
            request = Request(
                f"{self.base}/mcp",
                data=json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method}).encode(),
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream",
                    "MCP-Protocol-Version": PROTOCOL_VERSION,
                },
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                payload = json.loads(response.read())
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers["Mcp-Session-Id"], self.server.session_id)
                if method == "initialize":
                    self.assertEqual(payload["result"]["protocolVersion"], PROTOCOL_VERSION)
                else:
                    names = [tool["name"] for tool in payload["result"]["tools"]]
                    self.assertIn("plan_pursuit", names)

    def test_initialized_notification_is_accepted_without_body(self):
        request = Request(
            f"{self.base}/mcp",
            data=json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=2) as response:
            self.assertEqual(response.status, 202)
            self.assertEqual(response.headers["Mcp-Session-Id"], self.server.session_id)
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
            self.assertIn("Mcp-Session-Id", response.headers["Access-Control-Allow-Headers"])
            self.assertIn("MCP-Protocol-Version", response.headers["Access-Control-Allow-Headers"])

        blocked = Request(
            f"{self.base}/mcp",
            headers={"Origin": "https://attacker.example", "Access-Control-Request-Method": "POST"},
            method="OPTIONS",
        )
        with self.assertRaises(HTTPError) as raised:
            urlopen(blocked, timeout=2)
        self.assertEqual(raised.exception.code, 403)

    def test_invalid_origin_is_rejected_on_mcp_post_and_health_get(self):
        request = Request(
            f"{self.base}/mcp",
            data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode(),
            headers={"Origin": "https://attacker.example", "Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as raised_post:
            urlopen(request, timeout=2)
        self.assertEqual(raised_post.exception.code, 403)

        with self.assertRaises(HTTPError) as raised_get:
            urlopen(Request(f"{self.base}/health", headers={"Origin": "https://attacker.example"}), timeout=2)
        self.assertEqual(raised_get.exception.code, 403)

    def test_mcp_get_returns_405_when_server_does_not_offer_sse(self):
        request = Request(
            f"{self.base}/mcp",
            headers={"Accept": "text/event-stream", "Origin": "http://localhost:5173"},
            method="GET",
        )
        with self.assertRaises(HTTPError) as raised:
            urlopen(request, timeout=2)
        self.assertEqual(raised.exception.code, 405)

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
            {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
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
        planned, first_session = self.rpc(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "plan_pursuit",
                    "arguments": {"minimum_payout_usd": 100, "max_hours": 40},
                },
            }
        )
        case_id = planned["result"]["structuredContent"]["casefile"]["case_id"]
        initialized, second_session = self.rpc({"jsonrpc": "2.0", "id": 4, "method": "initialize"})
        self.assertEqual(initialized["result"]["protocolVersion"], PROTOCOL_VERSION)
        self.assertEqual(first_session, second_session)

        reviewed, third_session = self.rpc(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "review_pursuit_case",
                    "arguments": {"case_id": case_id, "focus": "evidence"},
                },
            }
        )
        value = reviewed["result"]["structuredContent"]
        self.assertEqual(third_session, first_session)
        self.assertTrue(value["case_found"])
        self.assertEqual(value["focus"], "evidence")
        self.assertIn("fixture_digest_sha256", value["evidence_card"])
        self.assertIn("verification_gaps", value["evidence_card"])


if __name__ == "__main__":
    unittest.main()
