"""Strands orchestration for the RewardRadar specialist team."""

from __future__ import annotations

from typing import Any

from strands import Agent
from strands.multiagent import GraphBuilder

from .tools import (
    load_demo_inventory,
    rank_demo_inventory,
    rank_opportunities,
    scan_execution_market,
    scan_opire,
    scan_superteam,
    score_demo_inventory,
    score_opportunity,
    verify_demo_inventory,
    verify_github_issue,
    verify_superteam_listing,
)


SYSTEM_PROMPT = """
You are RewardRadar, an evidence-first professional opportunity analyst.

Work through four explicit roles before recommending any paid task:
1. SCOUT: collect current inventory and normalize payout claims.
2. VERIFIER: open the canonical issue or task and check status, lock state, and activity.
3. RISK ANALYST: flag non-escrowed funds, crowded claims, vague acceptance criteria,
   region-locked payout rails, identity requirements, and suspicious aggregate totals.
4. ROI RANKER: call the deterministic scoring tool and compare expected value per hour.

Never treat an advertised amount as earned or guaranteed. Do not fabricate eligibility,
accounts, identities, work history, source status, or payout evidence. A recommendation
must cite the tool evidence that supports it. Prefer one defensible pursuit over a long
list of low-probability distractions.
""".strip()


def create_reward_radar(model: Any | None = None) -> Agent:
    """Create the Strands agent; model is injectable for Bedrock, OpenAI, or tests."""

    options: dict[str, Any] = {
        "name": "reward_radar",
        "system_prompt": SYSTEM_PROMPT,
        "tools": [
            scan_opire,
            scan_execution_market,
            scan_superteam,
            verify_github_issue,
            verify_superteam_listing,
            score_opportunity,
            rank_opportunities,
        ],
    }
    if model is not None:
        options["model"] = model
    return Agent(**options)


def _specialist(name: str, prompt: str, tools: list[Any], model: Any | None) -> Agent:
    options: dict[str, Any] = {
        "name": name,
        "description": prompt.split(".")[0],
        "system_prompt": f"{SYSTEM_PROMPT}\n\nYour current specialist role: {prompt}",
        "tools": tools,
    }
    if model is not None:
        options["model"] = model
    return Agent(**options)


def create_specialist_graph(model: Any | None = None, *, fixture_only: bool = False):
    """Build the four-node Strands graph shown in the product dashboard.

    ``fixture_only`` gives every role exactly one checked-in-data tool. That mode is
    stable for CI and hosted-model proof runs; the default keeps the live adapters
    available for an operator-requested audit.
    """

    scout_tools = [load_demo_inventory] if fixture_only else [
        load_demo_inventory,
        scan_opire,
        scan_execution_market,
        scan_superteam,
    ]
    verifier_tools = [verify_demo_inventory] if fixture_only else [
        verify_demo_inventory,
        verify_github_issue,
        verify_superteam_listing,
    ]
    risk_tools = [score_demo_inventory] if fixture_only else [
        score_demo_inventory,
        score_opportunity,
    ]
    roi_tools = [rank_demo_inventory] if fixture_only else [
        rank_demo_inventory,
        rank_opportunities,
    ]

    scout = _specialist(
        "scout",
        "Collect current inventory and normalize it without making a recommendation.",
        scout_tools,
        model,
    )
    verifier = _specialist(
        "verifier",
        "Cross-check marketplace claims against canonical GitHub or Superteam state and preserve evidence.",
        verifier_tools,
        model,
    )
    risk = _specialist(
        "risk_analyst",
        "Identify payment, competition, eligibility, scope, and manipulation risks.",
        risk_tools,
        model,
    )
    roi = _specialist(
        "roi_ranker",
        "Rank only verified candidates and issue a concise pursue, watch, or avoid verdict.",
        roi_tools,
        model,
    )

    builder = GraphBuilder()
    builder.set_graph_id("reward-radar-audit")
    builder.add_node(scout, "scout")
    builder.add_node(verifier, "verifier")
    builder.add_node(risk, "risk")
    builder.add_node(roi, "roi")
    builder.add_edge("scout", "verifier")
    builder.add_edge("verifier", "risk")
    builder.add_edge("risk", "roi")
    builder.set_entry_point("scout")
    builder.set_max_node_executions(8)
    builder.set_execution_timeout(120)
    return builder.build()


def audit(instruction: str, model: Any | None = None) -> str:
    """Run an end-to-end audit and return the model's evidence-backed decision."""

    agent = create_reward_radar(model=model)
    result = agent(instruction)
    return str(result)
