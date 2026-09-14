import unittest

from agent.demo_model import DemoModel
from agent.orchestrator import create_specialist_graph


class GraphExecutionTests(unittest.TestCase):
    def test_every_specialist_executes_its_disclosed_tool(self):
        graph = create_specialist_graph(model=DemoModel(), fixture_only=True)
        result = graph("Audit the fixture and return the strongest payable opportunity.")
        expected = {
            "scout": "load_demo_inventory",
            "verifier": "verify_demo_inventory",
            "risk": "score_demo_inventory",
            "roi": "rank_demo_inventory",
        }

        for node_id, expected_tool in expected.items():
            messages = graph.nodes[node_id].executor.messages
            tool_names = [
                block["toolUse"]["name"]
                for message in messages
                for block in message.get("content", [])
                if isinstance(block, dict) and "toolUse" in block
            ]
            result_count = sum(
                1
                for message in messages
                for block in message.get("content", [])
                if isinstance(block, dict) and "toolResult" in block
            )
            self.assertIn(expected_tool, tool_names)
            self.assertGreaterEqual(result_count, 1)

        self.assertIn("PURSUE", str(result))

    def test_fixture_mode_exposes_exactly_one_checked_in_data_tool_per_node(self):
        graph = create_specialist_graph(model=DemoModel(), fixture_only=True)
        expected = {
            "scout": ["load_demo_inventory"],
            "verifier": ["verify_demo_inventory"],
            "risk": ["score_demo_inventory"],
            "roi": ["rank_demo_inventory"],
        }

        for node_id, tool_names in expected.items():
            self.assertEqual(graph.nodes[node_id].executor.tool_names, tool_names)


if __name__ == "__main__":
    unittest.main()
