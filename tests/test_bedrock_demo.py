import contextlib
import io
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent import bedrock_demo
from strands.multiagent import Status


class BedrockDemoTests(unittest.TestCase):
    @patch("agent.bedrock_demo.create_specialist_graph")
    @patch("agent.bedrock_demo.BedrockModel")
    def test_cli_builds_explicit_bedrock_model_and_runs_graph(self, model_class, graph_factory):
        model = model_class.return_value
        completed = SimpleNamespace(
            status=Status.COMPLETED,
            failed_nodes=[],
            completed_nodes=4,
            total_nodes=4,
            execution_order=["scout", "verifier", "risk", "roi"],
            accumulated_usage={"inputTokens": 10, "outputTokens": 5, "totalTokens": 15},
        )
        graph = MagicMock(return_value=completed)
        graph_factory.return_value = graph
        stdout = io.StringIO()
        stderr = io.StringIO()

        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            bedrock_demo.main(
                [
                    "--model-id",
                    "example.model-v1:0",
                    "--region",
                    "us-east-1",
                    "--instruction",
                    "Audit fixture",
                ]
            )

        model_class.assert_called_once_with(
            model_id="example.model-v1:0",
            temperature=0,
            max_tokens=512,
            region_name="us-east-1",
        )
        graph_factory.assert_called_once_with(model=model, fixture_only=True)
        graph.assert_called_once_with("Audit fixture")
        self.assertIn("Status.COMPLETED", stdout.getvalue())
        self.assertIn("BEDROCK RUN STARTING", stderr.getvalue())
        self.assertIn("BEDROCK RUN COMPLETED", stderr.getvalue())
        self.assertIn("scout,verifier,risk,roi", stderr.getvalue())

    @patch("agent.bedrock_demo.BedrockModel")
    def test_model_uses_sdk_region_chain_when_region_is_absent(self, model_class):
        bedrock_demo.create_bedrock_model("example.model-v1:0")

        model_class.assert_called_once_with(
            model_id="example.model-v1:0",
            temperature=0,
            max_tokens=512,
        )

    @patch("agent.bedrock_demo.create_specialist_graph")
    @patch("agent.bedrock_demo.BedrockModel")
    def test_failed_graph_never_prints_completion(self, model_class, graph_factory):
        graph_factory.return_value = MagicMock(
            return_value=SimpleNamespace(
                status=Status.FAILED,
                failed_nodes=["verifier"],
            )
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaisesRegex(RuntimeError, "did not complete"):
                bedrock_demo.main(["--model-id", "example.model-v1:0"])

        self.assertIn("BEDROCK RUN STARTING", stderr.getvalue())
        self.assertNotIn("BEDROCK RUN COMPLETED", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
