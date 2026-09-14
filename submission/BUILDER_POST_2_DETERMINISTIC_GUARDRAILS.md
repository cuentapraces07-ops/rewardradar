# Agents for Humans: Putting Deterministic Guardrails Inside a Strands Agent Graph

> Publication status: draft. Prepared for the optional builder.aws bonus; not yet published.

Large language models are good at comparing messy evidence and explaining tradeoffs. They are not the right place to hide the arithmetic that decides whether a professional should spend ten hours on a speculative reward.

That design constraint shaped RewardRadar, a Strands multi-agent system for auditing paid technical opportunities. Ordinary Python owns the risk multipliers, expected-value arithmetic, and final thresholds. Evidence fields and any explicit base probability remain reviewable inputs rather than hidden model facts.

## The split between reasoning and policy

Each normalized opportunity becomes a `Candidate` with explicit fields: advertised payout, estimated effort, canonical status, visible claimers, lock state, escrow evidence, sponsor verification, acceptance clarity, repository activity, payout-rail readiness, deadline, and an optional disclosed base probability.

The deterministic function applies conservative rules. A closed canonical issue sets payment probability to zero. A locked issue receives a severe multiplier. More claimers reduce the probability monotonically. Missing payout setup and ambiguous acceptance criteria reduce it further. Expected value and expected hourly value are calculated from the resulting probability.

The model cannot alter the arithmetic inside the scoring tool. It can still supply incorrect evidence fields, so RewardRadar retains canonical URLs and requires evidence review:

```python
@tool
def score_opportunity(candidate_json: str) -> str:
    candidate = Candidate(**json.loads(candidate_json))
    return json.dumps(assess_candidate(candidate).to_dict(), sort_keys=True)
```

The ROI specialist can interpret the returned evidence, but the tool result remains reproducible and inspectable.

## Tests are part of the product argument

I wanted the repository to prove the claims that matter most. The test suite checks that:

- a closed issue is always avoided, even if the headline payout is enormous;
- adding competitors lowers payment probability;
- ranking uses payment-adjusted hourly return rather than raw prize size;
- a disclosed probability is not silently inflated by optimistic bonuses;
- an inventory whose total cannot reach the user's minimum is rejected;
- every specialist in the four-node Strands graph actually executes its disclosed tool and records a tool result;
- non-USD tokens are not mislabeled as dollars;
- costly social, capital, and mainnet requirements are extracted from canonical competition details;
- fictional phone-number ranges remain blocked from optional live verification.

Those are not generic “agent works” assertions. They encode the failure modes that would waste real human time or create false confidence.

## A reproducible model adapter without a fake cloud claim

The demo needed to run for judges and continuous integration without requiring a paid model key. I implemented `DemoModel`, a small adapter that satisfies the Strands model interface and makes one prescribed tool call for each specialist. It then returns a concise role-specific result.

This is not presented as a foundation model. Its purpose is to prove the actual Strands execution path: agent construction, graph handoff, tool invocation, tool results, and final output. Running `python -m agent.demo` prints both the deterministic ranking and a tool-execution ledger for Scout, Verifier, Risk Analyst, and ROI Ranker.

The same graph accepts any compatible Strands model. The repository includes `agent.bedrock_demo`, which configures the SDK’s Amazon Bedrock provider through the standard AWS credential chain while retaining the same tools and deterministic formulas. The submitted version does not claim a successful Bedrock run until corresponding runtime evidence exists.

## Bounded execution matters

Agentic systems need stopping conditions. RewardRadar sets a graph execution timeout and a maximum node-execution count. Source tools use request timeouts and narrow URL validators. Inputs such as marketplace descriptions, HTML, filenames, and API responses are treated as data, not instructions.

The optional CALL-E verification extension follows the same philosophy. It defaults to a network-free preview, masks the destination, binds the intent to an idempotency key, requires exact confirmation before one call, and still refuses to label a completed call as verified payment. A lead is not a settlement.

## What the model is still good for

Deterministic formulas do not eliminate the usefulness of a hosted model. When configured, the specialists can compare why two superficially similar opportunities differ, identify ambiguous scope, notice mismatched deadlines, and produce a concise recommendation. The formulas remain fixed, but the evidence inputs and synthesis still require source-backed review.

This architecture is reusable beyond bounties. Any professional workflow with messy inputs and irreversible consequences can split responsibilities the same way: models for synthesis and challenge; tools for source state; deterministic code for hard policy; humans for legal, identity, and financial decisions.

That is how I want agents to work for humans: flexible where judgment helps, rigid where false confidence hurts.

---

Disclosure: RewardRadar and this draft were developed with substantial assistance from OpenAI Codex. The project uses the open-source Strands Agents SDK. No Amazon Bedrock or AgentCore deployment is claimed in the submitted build.
