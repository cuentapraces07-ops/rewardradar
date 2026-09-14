"""A tiny deterministic Strands model used only for repeatable demos and CI.

Production can inject any Strands-supported model. This adapter lets judges run the
actual four-node Graph without AWS credentials and without hiding an API call behind
the demo.
"""

from __future__ import annotations

from collections.abc import AsyncIterable
from typing import Any

from strands.models.model import Model


class DemoModel(Model):
    def __init__(self) -> None:
        self.config = {"model_id": "rewardradar-deterministic-demo", "context_window_limit": 4096}

    def update_config(self, **model_config: Any) -> None:
        self.config.update(model_config)

    def get_config(self) -> dict[str, Any]:
        return self.config

    async def structured_output(self, output_model, prompt, system_prompt=None, **kwargs):
        raise NotImplementedError("The deterministic demo does not emit structured model output")
        yield  # pragma: no cover

    async def stream(
        self,
        messages,
        tool_specs=None,
        system_prompt=None,
        *,
        tool_choice=None,
        system_prompt_content=None,
        invocation_state=None,
        cancel_signal=None,
        **kwargs,
    ) -> AsyncIterable[dict]:
        prompt = (system_prompt or "").lower()
        has_tool_result = any(
            "toolResult" in block
            for message in messages
            for block in message.get("content", [])
            if isinstance(block, dict)
        )
        if "current specialist role: collect" in prompt:
            answer = "SCOUT complete: loaded 4 representative candidates from the disclosed fixture."
            tool_name = "load_demo_inventory"
        elif "current specialist role: cross-check" in prompt:
            answer = "VERIFIER complete: preserved canonical status, lock, URL, and competition evidence for all 4."
            tool_name = "verify_demo_inventory"
        elif "current specialist role: identify" in prompt:
            answer = "RISK complete: locked issues, crowded claims, and non-escrowed rewards dominate the inventory."
            tool_name = "score_demo_inventory"
        elif "current specialist role: rank" in prompt:
            answer = "ROI complete: PURSUE the cash hackathon; AVOID the sub-floor market, locked crowded bounty, and capital-gated social competition."
            tool_name = "rank_demo_inventory"
        else:
            answer = "RewardRadar audit complete."
            tool_name = "load_demo_inventory"

        yield {"messageStart": {"role": "assistant"}}
        if not has_tool_result:
            tool_use_id = f"demo_{tool_name}"
            yield {
                "contentBlockStart": {
                    "start": {"toolUse": {"name": tool_name, "toolUseId": tool_use_id}}
                }
            }
            yield {"contentBlockDelta": {"delta": {"toolUse": {"input": "{}"}}}}
            stop_reason = "tool_use"
        else:
            yield {"contentBlockStart": {"start": {}}}
            yield {"contentBlockDelta": {"delta": {"text": answer}}}
            stop_reason = "end_turn"
        yield {"contentBlockStop": {}}
        yield {"messageStop": {"stopReason": stop_reason}}
        yield {
            "metadata": {
                "usage": {"inputTokens": 0, "outputTokens": len(answer.split()), "totalTokens": len(answer.split())},
                "metrics": {"latencyMs": 1},
            }
        }
