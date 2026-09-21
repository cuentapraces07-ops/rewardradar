"""Offline HTTP contract tests for the Alexa+ MCP endpoint.

The Amazon rules require a working MCP server.  These tests bind only to an
ephemeral loopback port and never contact an external service.
"""

from __future__ import annotations

import json
import threading
import unittest
from urllib.request import Request, urlopen

from agent.alexa_mcp_server import MCPServer, PROTOCOL_VERSION


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

    def test_health_is_local_and_explicit(self):
        with urlopen(f"{self.base}/health", timeout=2) as response:
            payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertTrue(payload["ok"])
            self.assertEqual(payload["mode"], "fixture")
            self.assertEqual(response.headers["Mcp-Session-Id"], self.server.session_id)

    def test_streamable_http_initialize_and_tools_list(self):
        for request_id, method in ((1, "initialize"), (2, "tools/list")):
            request = Request(
                f"{self.base}/mcp",
                data=json.dumps({"jsonrpc": "2.0", "id": request_id, "method": method}).encode(),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
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


if __name__ == "__main__":
    unittest.main()
