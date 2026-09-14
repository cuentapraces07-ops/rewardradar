"""Reproducible local demonstration that does not need a paid model key."""

from __future__ import annotations

import json
from pathlib import Path

from .core import Candidate, rank_candidates
from .demo_model import DemoModel
from .orchestrator import create_specialist_graph


def main() -> None:
    fixture_path = Path(__file__).parents[1] / "data" / "demo_candidates.json"
    candidates = [Candidate(**item) for item in json.loads(fixture_path.read_text(encoding="utf-8"))]
    decisions = rank_candidates(candidates)
    print("DETERMINISTIC RANKING")
    print(json.dumps([decision.to_dict() for decision in decisions], indent=2))
    print("\nSTRANDS GRAPH RUN")
    graph = create_specialist_graph(model=DemoModel(), fixture_only=True)
    result = graph("Audit the supplied fixture and return the strongest payable opportunity.")
    print(result)
    print("\nTOOL EXECUTION LEDGER")
    for node_id, node in graph.nodes.items():
        tool_names = [
            block["toolUse"]["name"]
            for message in node.executor.messages
            for block in message.get("content", [])
            if isinstance(block, dict) and "toolUse" in block
        ]
        tool_results = sum(
            1
            for message in node.executor.messages
            for block in message.get("content", [])
            if isinstance(block, dict) and "toolResult" in block
        )
        print(f"{node_id}: tools={','.join(tool_names)} results={tool_results}")


if __name__ == "__main__":
    main()
