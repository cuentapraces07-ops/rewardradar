# Agents for Humans: Building an Agent That Distrusts Its Own Marketplace

> Publication status: draft. Prepared for the optional builder.aws bonus; not yet published.

The fastest way to make a reward-finding agent look impressive is to show a very large number. The fastest way to make it useful is to distrust that number.

I built RewardRadar for independent developers and open-source contributors who need to decide where to spend limited focused time. Its job is not to collect the biggest bounty feed. Its job is to answer a narrower professional question: **which opportunity is worth pursuing after payment, competition, eligibility, and source-state risk are considered?**

The project uses the Strands Agents SDK as a four-specialist graph:

```text
Scout -> Verifier -> Risk Analyst -> ROI Ranker
```

Each role owns one kind of uncertainty. Scout normalizes marketplace rows. Verifier opens the canonical GitHub issue or competition record. Risk Analyst measures crowding, payout friction, unclear acceptance criteria, and costly eligibility gates. ROI Ranker applies a deterministic expected-value function and emits a `pursue`, `watch`, or `avoid` decision.

## Why the canonical source is a separate tool

Marketplace data is useful for discovery, but it is not authoritative. A row can outlive the issue it references. A reward can be described as available even when the underlying issue is closed or locked. A large pending amount can still require a sponsor to choose and pay a claimant later.

RewardRadar therefore gives the Verifier its own Strands tool. For a GitHub URL, the tool checks the public GitHub API and preserves the issue state, lock status, comment count, update time, and canonical URL. The model receives that evidence alongside an instruction not to fabricate it; source URLs remain visible so its inputs and conclusions can be reviewed.

That boundary paid off in a time-stamped capture on September 11, 2026. The marketplace endpoint returned 30 advertised rows. Only eight mapped to canonical GitHub issues that were still open; 22 were closed, deleted, or unverifiable. One seemingly conventional reward with no visible solvers advertised $1,500, but the canonical request returned HTTP 410 because the original issue had been deleted. An even larger displayed outlier was already closed at its canonical source. A feed-only assistant could have recommended either. The deterministic audit pipeline rejected them before any implementation time was spent.

The source package preserves the raw result in `data/audit-2026-09-11.json`. The point is not that every marketplace row is bad. The point is that discovery and verification are different jobs and should be implemented as different trust boundaries.

## Why this is a graph instead of one long prompt

A single prompt tends to mix collection, judgment, and presentation. That makes it difficult to tell whether a conclusion came from evidence or fluent synthesis. In RewardRadar, each specialist has a small tool set and a specific instruction:

- Scout may collect and normalize, but must not recommend.
- Verifier may check source state and preserve evidence.
- Risk Analyst may identify failure modes and economic friction.
- ROI Ranker may compare only verified candidates.

`GraphBuilder` connects those nodes in order and caps total node executions and wall-clock time. The graph is executable, not decorative. The credential-free demonstration uses a deterministic Strands-compatible adapter with one prescribed tool call per node, so judges can verify orchestration without cloud credentials. `agent.bedrock_demo` injects a real Amazon Bedrock model without changing the graph or deterministic formulas; no successful hosted invocation is claimed until runtime evidence is captured.

## The human stays responsible for the irreversible parts

RewardRadar can recommend that a professional pursue a contest or issue. It cannot make eligibility true, promise that a sponsor will pay, or turn a pending reward into income. It also does not create identities, accept legal rules, or configure financial accounts.

This is deliberate product design. The agent does the repetitive work humans are bad at doing consistently: cross-checking feeds, normalizing evidence, calculating comparable returns, and recording why a tempting option was rejected. The human retains decisions involving identity, contracts, public representation, and payment details.

That division is what “agents for humans” means to me. The system should absorb tedious verification without blurring responsibility. An evidence-backed “avoid” can be more valuable than another attractive card in a feed.

## What I would build next

The next version would add signed marketplace receipts, sponsor payment histories, region-aware payout compatibility, and alerts that trigger only after an opportunity crosses a user-defined expected-value threshold. Amazon Bedrock AgentCore would be a natural deployment target for isolating the runtime and exposing a durable invocation endpoint, but it is not part of the submitted running build and I do not claim otherwise.

RewardRadar's lesson is simple: a useful professional agent should not merely browse faster. It should make uncertainty inspectable and protect the user's time.

---

Disclosure: RewardRadar and this draft were developed with substantial assistance from OpenAI Codex. The project uses the open-source Strands Agents SDK. No Amazon Bedrock or AgentCore deployment is claimed in the submitted build.
