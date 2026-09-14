"""Run the RewardRadar specialist graph with a real Amazon Bedrock model.

This entry point exposes no credential flags or credential files and delegates
authentication to the standard AWS SDK chain. The credential-free ``agent.demo``
remains the reproducible CI path; this module is the explicit hosted-model path.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from typing import Any

from strands.models import BedrockModel
from strands.multiagent import Status

from .orchestrator import create_specialist_graph


DEFAULT_MODEL_ID = "global.anthropic.claude-sonnet-4-6"
DEFAULT_INSTRUCTION = (
    "Audit only the committed fixture. Each role must call its single registered "
    "fixture tool, preserve its output as evidence, and return the strongest payable "
    "opportunity without treating any advertised amount as earned."
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute RewardRadar's four-node Strands graph on Amazon Bedrock."
    )
    parser.add_argument(
        "--model-id",
        default=os.getenv("REWARDRADAR_BEDROCK_MODEL_ID", DEFAULT_MODEL_ID),
        help="Bedrock model or inference-profile ID.",
    )
    parser.add_argument(
        "--region",
        default=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"),
        help="AWS region; otherwise the standard SDK configuration is used.",
    )
    parser.add_argument(
        "--instruction",
        default=DEFAULT_INSTRUCTION,
        help="Audit instruction passed to the specialist graph.",
    )
    return parser


def create_bedrock_model(model_id: str, region: str | None = None) -> BedrockModel:
    """Create a conservative Bedrock provider without reading custom secrets."""

    options: dict[str, Any] = {
        "model_id": model_id,
        "temperature": 0,
        "max_tokens": 512,
    }
    if region:
        options["region_name"] = region
    return BedrockModel(**options)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    model = create_bedrock_model(args.model_id, args.region)
    region_label = args.region or "AWS SDK default"
    print(
        f"BEDROCK RUN STARTING model={args.model_id} region={region_label}",
        file=sys.stderr,
    )
    graph = create_specialist_graph(model=model, fixture_only=True)
    result = graph(args.instruction)
    if result.status is not Status.COMPLETED:
        raise RuntimeError(
            "Bedrock graph did not complete: "
            f"status={result.status} failed_nodes={result.failed_nodes}"
        )
    print(result)
    print(
        "BEDROCK RUN COMPLETED "
        f"nodes={result.completed_nodes}/{result.total_nodes} "
        f"order={','.join(result.execution_order)} "
        f"usage={json.dumps(result.accumulated_usage, sort_keys=True)}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
