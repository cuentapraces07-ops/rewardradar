import unittest

from agent.alexa_mcp_server import PROTOCOL_VERSION, handle_rpc


class AlexaMCPServerTests(unittest.TestCase):
    def test_initialize_discloses_protocol_and_server(self):
        response = handle_rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        self.assertEqual(response["result"]["protocolVersion"], PROTOCOL_VERSION)
        self.assertEqual(response["result"]["serverInfo"]["name"], "rewardradar-alexa-plus")

    def test_tools_list_is_explicit(self):
        response = handle_rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        names = [item["name"] for item in response["result"]["tools"]]
        self.assertEqual(
            names,
            ["search_rewards", "verify_funding", "summarize_submission_status", "plan_pursuit"],
        )

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
        self.assertLessEqual(len(value["results"]), 2)
        self.assertIn("Fixture replay", value["disclosure"])

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

    def test_plan_pursuit_is_bounded_and_read_only(self):
        response = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "plan_pursuit",
                    "arguments": {"minimum_payout_usd": 100, "max_hours": 40},
                },
            }
        )
        value = response["result"]["structuredContent"]
        self.assertEqual(value["recommendation"]["title"], "Agents for Humans — Professional Agents")
        self.assertEqual(value["safety"]["external_action"], "owner_confirmation_required")
        self.assertFalse(value["safety"]["payout_guaranteed"])
        self.assertIn("canonical source", " ".join(value["next_steps"]))

    def test_plan_pursuit_reports_no_match_without_inventing_work(self):
        response = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 6,
                "method": "tools/call",
                "params": {
                    "name": "plan_pursuit",
                    "arguments": {"query": "does-not-exist", "max_hours": "not-a-number"},
                },
            }
        )
        value = response["result"]["structuredContent"]
        self.assertIsNone(value["recommendation"])
        self.assertEqual(value["constraints"]["max_hours"], 8)
        self.assertFalse(value["safety"]["payout_guaranteed"])

    def test_initialized_notification_has_no_response(self):
        self.assertIsNone(handle_rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}))


if __name__ == "__main__":
    unittest.main()
