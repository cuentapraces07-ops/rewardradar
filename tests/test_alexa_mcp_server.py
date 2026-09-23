import unittest

from agent.alexa_mcp_server import CaseStore, PROTOCOL_VERSION, handle_rpc


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
            [
                "search_rewards",
                "verify_funding",
                "summarize_submission_status",
                "plan_pursuit",
                "review_pursuit_case",
            ],
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

    def test_case_can_resume_after_a_new_initialize_without_storing_query_text(self):
        store = CaseStore(ttl_seconds=60)
        plan = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "plan_pursuit",
                    "arguments": {"query": "private words must not persist", "minimum_payout_usd": 100, "max_hours": 40},
                },
            },
            store,
        )["result"]["structuredContent"]
        case_id = plan["casefile"]["case_id"]
        self.assertEqual(len(case_id), 32)
        self.assertNotIn("query", store.get(case_id))

        initialized = handle_rpc({"jsonrpc": "2.0", "id": 8, "method": "initialize"}, store)
        self.assertEqual(initialized["result"]["protocolVersion"], PROTOCOL_VERSION)
        review = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 9,
                "method": "tools/call",
                "params": {
                    "name": "review_pursuit_case",
                    "arguments": {"case_id": case_id, "focus": "comparison"},
                },
            },
            store,
        )["result"]["structuredContent"]
        self.assertTrue(review["case_found"])
        self.assertEqual(review["focus"], "comparison")
        self.assertEqual(review["constraints"], {"max_hours": 40.0, "minimum_payout_usd": 100.0})
        self.assertIn("alternatives", review["evidence_card"])
        self.assertFalse(review["safety"]["payout_guaranteed"])

    def test_case_isolation_and_expiry_fail_closed(self):
        now = [100.0]
        store = CaseStore(ttl_seconds=2, clock=lambda: now[0])

        def open_case(request_id, minimum_payout):
            return handle_rpc(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {
                        "name": "plan_pursuit",
                        "arguments": {"minimum_payout_usd": minimum_payout, "max_hours": 40},
                    },
                },
                store,
            )["result"]["structuredContent"]["casefile"]["case_id"]

        first_case = open_case(10, 100)
        second_case = open_case(11, 1_000_000)
        self.assertNotEqual(first_case, second_case)
        second_review = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 12,
                "method": "tools/call",
                "params": {"name": "review_pursuit_case", "arguments": {"case_id": second_case}},
            },
            store,
        )["result"]["structuredContent"]
        self.assertEqual(second_review["constraints"]["minimum_payout_usd"], 1_000_000.0)
        self.assertIsNone(second_review["evidence_card"]["recommendation"])

        now[0] += 3
        expired = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 13,
                "method": "tools/call",
                "params": {"name": "review_pursuit_case", "arguments": {"case_id": first_case}},
            },
            store,
        )["result"]["structuredContent"]
        self.assertFalse(expired["case_found"])
        self.assertEqual(expired["state"], "expired_or_unknown")

    def test_case_rejects_unknown_focus_without_action(self):
        response = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 14,
                "method": "tools/call",
                "params": {"name": "review_pursuit_case", "arguments": {"case_id": "0" * 32, "focus": "send"}},
            },
            CaseStore(),
        )["result"]["structuredContent"]
        self.assertFalse(response["case_found"])
        self.assertIn("focus must be", response["reason"])
        self.assertFalse(response["safety"]["payout_guaranteed"])

    def test_case_rejects_stale_fixture_evidence(self):
        store = CaseStore()
        stale_case, _ = store.create({"fixture_digest_sha256": "0" * 64})
        response = handle_rpc(
            {
                "jsonrpc": "2.0",
                "id": 15,
                "method": "tools/call",
                "params": {"name": "review_pursuit_case", "arguments": {"case_id": stale_case}},
            },
            store,
        )["result"]["structuredContent"]
        self.assertFalse(response["case_found"])
        self.assertEqual(response["state"], "fixture_changed")
        self.assertIn("not reused", response["disclosure"])

    def test_initialized_notification_has_no_response(self):
        self.assertIsNone(handle_rpc({"jsonrpc": "2.0", "method": "notifications/initialized"}))


if __name__ == "__main__":
    unittest.main()
