import http.client
import json
import threading
import unittest

from agent.alexa_mcp_server import DEFAULT_ALLOWED_ORIGINS, MCPServer, PROTOCOL_VERSION, _normalize_origin, handle_rpc


class AlexaMCPServerTests(unittest.TestCase):
    def test_initialize_discloses_protocol_and_server(self):
        response = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"},
                },
            }
        )
        self.assertEqual(response["result"]["protocolVersion"], PROTOCOL_VERSION)
        self.assertEqual(response["result"]["serverInfo"]["name"], "rewardradar-alexa-plus")

    def test_tools_list_is_explicit(self):
        response = handle_rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [item["name"] for item in response["result"]["tools"]]
        self.assertEqual(names, ["search_rewards", "verify_funding", "summarize_submission_status"])

    def test_search_returns_fixture_and_disclosure(self):
        response = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "search_rewards", "arguments": {"limit": 2}},
            }
        )
        value = response["result"]["structuredContent"]
        self.assertEqual(value["mode"], "fixture")
        self.assertEqual(value["data_as_of"], "2026-09-10")
        self.assertLessEqual(len(value["results"]), 2)
        self.assertIn("Fixture replay", value["disclosure"])

    def test_submission_status_distinguishes_submitted_from_paid(self):
        response = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "summarize_submission_status", "arguments": {"track": "Alexa+"}},
            }
        )
        value = response["result"]["structuredContent"]
        self.assertEqual(value["submission"], "submitted")
        self.assertEqual(value["award"], "not announced")
        self.assertEqual(value["payment"], "not received")
        self.assertIn("devpost.com/software", value["submission_url"])

    def test_other_track_is_not_assumed_submitted(self):
        response = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {"name": "summarize_submission_status", "arguments": {"track": "Open Source"}},
            }
        )
        value = response["result"]["structuredContent"]
        self.assertIn("not confirmed", value["submission"])
        self.assertEqual(value["payment"], "not received")

    def test_unknown_tool_does_not_execute(self):
        response = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "bind_wallet", "arguments": {}},
            }
        )
        self.assertEqual(response["error"]["code"], -32602)

    def test_initialized_notification_has_no_response(self):
        self.assertIsNone(handle_rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_invalid_json_rpc_and_tool_arguments_fail_as_protocol_errors(self):
        self.assertEqual(handle_rpc({"jsonrpc": "1.0", "id": 1, "method": "tools/list"})["error"]["code"], -32600)
        invalid_params = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "search_rewards", "arguments": []},
            }
        )
        self.assertEqual(invalid_params["error"]["code"], -32602)

    def test_local_origin_defaults_are_narrow_and_origins_are_exact(self):
        self.assertEqual(
            DEFAULT_ALLOWED_ORIGINS,
            frozenset({"http://localhost:5173", "http://127.0.0.1:5173"}),
        )
        self.assertEqual(_normalize_origin("HTTPS://Example.COM:443"), "https://example.com")
        for origin in (
            "*",
            "https://example.com/path",
            "https://user@example.com",
            "http://example.com:0",
        ):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                _normalize_origin(origin)


class AlexaMCPTransportTests(unittest.TestCase):
    origin = "http://demo.example"

    @classmethod
    def setUpClass(cls):
        cls.server = MCPServer(("127.0.0.1", 0), allowed_origins=[cls.origin])
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server_thread.join(timeout=2)
        cls.server.server_close()

    def request(self, method, path="/mcp", *, headers=None, payload=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        body = json.dumps(payload) if payload is not None else None
        connection.request(method, path, body=body, headers=headers or {})
        response = connection.getresponse()
        result = (response.status, {key.lower(): value for key, value in response.getheaders()}, response.read())
        connection.close()
        return result

    def post_headers(self, *, session_id=None, origin=None, accept="application/json, text/event-stream", protocol=PROTOCOL_VERSION, content_type="application/json"):
        headers = {
            "Accept": accept,
            "Content-Type": content_type,
            "Origin": origin or self.origin,
        }
        if protocol is not None:
            headers["MCP-Protocol-Version"] = protocol
        if session_id is not None:
            headers["Mcp-Session-Id"] = session_id
        return headers

    def initialize(self):
        return self.request(
            "POST",
            headers=self.post_headers(),
            payload={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "transport-test", "version": "1.0"},
                },
            },
        )

    def test_streamable_http_handshake_notification_and_tool_call(self):
        status, headers, body = self.initialize()
        self.assertEqual(status, 200)
        self.assertEqual(headers["content-type"], "application/json")
        self.assertEqual(headers["access-control-allow-origin"], self.origin)
        initialized = json.loads(body)
        self.assertEqual(initialized["result"]["protocolVersion"], PROTOCOL_VERSION)
        session_id = headers["mcp-session-id"]
        self.assertGreaterEqual(len(session_id), 32)

        before_notification = self.request(
            "POST",
            headers=self.post_headers(session_id=session_id),
            payload={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        self.assertEqual(before_notification[0], 400)

        status, headers, body = self.request(
            "POST",
            headers=self.post_headers(session_id=session_id),
            payload={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        self.assertEqual(status, 202)
        self.assertEqual(body, b"")
        self.assertEqual(headers["mcp-session-id"], session_id)

        status, headers, body = self.request(
            "POST",
            headers=self.post_headers(session_id=session_id),
            payload={"jsonrpc": "2.0", "id": 3, "method": "tools/list"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(headers["mcp-session-id"], session_id)
        tools = json.loads(body)["result"]["tools"]
        self.assertEqual([tool["name"] for tool in tools], ["search_rewards", "verify_funding", "summarize_submission_status"])

        status, _, body = self.request(
            "POST",
            headers=self.post_headers(session_id=session_id),
            payload={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {"name": "summarize_submission_status", "arguments": {"track": "Alexa+"}},
            },
        )
        self.assertEqual(status, 200)
        result = json.loads(body)["result"]["structuredContent"]
        self.assertEqual(result["submission"], "submitted")
        self.assertEqual(result["payment"], "not received")

        deleted = self.request("DELETE", headers=self.post_headers(session_id=session_id))
        self.assertEqual(deleted[0], 204)
        expired = self.request(
            "POST",
            headers=self.post_headers(session_id=session_id),
            payload={"jsonrpc": "2.0", "id": 5, "method": "tools/list"},
        )
        self.assertEqual(expired[0], 404)

    def test_origin_allowlist_rejects_untrusted_browser_origin(self):
        status, headers, _ = self.request(
            "POST",
            headers=self.post_headers(origin="https://attacker.example"),
            payload={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        )
        self.assertEqual(status, 403)
        self.assertNotIn("access-control-allow-origin", headers)

    def test_cors_preflight_reflects_only_an_explicitly_allowed_origin(self):
        status, headers, body = self.request(
            "OPTIONS",
            headers={
                "Origin": self.origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,accept,mcp-protocol-version,mcp-session-id",
            },
        )
        self.assertEqual(status, 204)
        self.assertEqual(body, b"")
        self.assertEqual(headers["access-control-allow-origin"], self.origin)
        self.assertIn("mcp-session-id", headers["access-control-allow-headers"].lower())

        denied = self.request("OPTIONS", headers={"Origin": "https://attacker.example"})
        self.assertEqual(denied[0], 403)

    def test_get_endpoint_returns_405_when_server_sent_events_are_not_supported(self):
        status, headers, body = self.request(
            "GET",
            headers={"Origin": self.origin, "Accept": "text/event-stream"},
        )
        self.assertEqual(status, 405)
        self.assertEqual(body, b"")
        self.assertIn("GET", headers["allow"])
        self.assertEqual(headers["access-control-allow-origin"], self.origin)

        no_accept = self.request("GET", headers={"Origin": self.origin})
        self.assertEqual(no_accept[0], 406)

    def test_post_requires_json_and_both_streamable_http_accept_types(self):
        payload = {"jsonrpc": "2.0", "id": 1, "method": "initialize"}
        wrong_accept = self.request(
            "POST",
            headers=self.post_headers(accept="application/json"),
            payload=payload,
        )
        self.assertEqual(wrong_accept[0], 406)

        wrong_content_type = self.request(
            "POST",
            headers=self.post_headers(content_type="text/plain"),
            payload=payload,
        )
        self.assertEqual(wrong_content_type[0], 415)

    def test_protocol_version_and_session_are_required_after_initialize(self):
        status, headers, _ = self.initialize()
        self.assertEqual(status, 200)
        session_id = headers["mcp-session-id"]
        ready = self.request(
            "POST",
            headers=self.post_headers(session_id=session_id),
            payload={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        self.assertEqual(ready[0], 202)

        missing_session = self.request(
            "POST",
            headers=self.post_headers(),
            payload={"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        )
        self.assertEqual(missing_session[0], 400)

        missing_protocol = self.request(
            "POST",
            headers=self.post_headers(session_id=session_id, protocol=None),
            payload={"jsonrpc": "2.0", "id": 3, "method": "tools/list"},
        )
        self.assertEqual(missing_protocol[0], 400)

        unsupported_protocol = self.request(
            "POST",
            headers=self.post_headers(session_id=session_id, protocol="2024-11-05"),
            payload={"jsonrpc": "2.0", "id": 4, "method": "tools/list"},
        )
        self.assertEqual(unsupported_protocol[0], 400)

    def test_expired_session_is_404_and_initialize_without_protocol_header_is_supported(self):
        status, headers, _ = self.request(
            "POST",
            headers=self.post_headers(protocol=None),
            payload={
                "jsonrpc": "2.0",
                "id": 7,
                "method": "initialize",
                "params": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "transport-test", "version": "1.0"},
                },
            },
        )
        self.assertEqual(status, 200)
        session_id = headers["mcp-session-id"]
        with self.server._sessions_lock:
            created_at, _ = self.server._sessions[session_id]
            self.server._sessions[session_id] = (created_at - 3601, False)
        expired = self.request(
            "POST",
            headers=self.post_headers(session_id=session_id),
            payload={"jsonrpc": "2.0", "method": "notifications/initialized"},
        )
        self.assertEqual(expired[0], 404)


if __name__ == "__main__":
    unittest.main()
