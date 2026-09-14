# Agents for Humans: The Deleted $1,500 Bounty That Looked Like the Best Choice

> Publication status: draft. Prepared for the optional builder.aws bonus; not yet published.

On September 11, 2026, a public bounty marketplace showed an apparently attractive opportunity: $1,500, zero visible solvers, and an open status. For a developer trying to earn at least $100, it looked like the obvious next move.

The underlying GitHub issue had been deleted.

This small incident captures why I built RewardRadar with the Strands Agents SDK. The difficult part of finding paid work is not retrieving rows. It is deciding which claims deserve a professional's time.

## Reproducing the result

RewardRadar's evidence capture follows two stages:

1. fetch the marketplace inventory;
2. verify every standard GitHub issue URL against the canonical GitHub API.

The September 11 run returned 30 advertised marketplace rows. Only eight resolved to GitHub issues that were still open. Twenty-two were closed, deleted, or unverifiable. The $1,500 row had no listed claimant and no listed person trying it, but the canonical API returned HTTP 410. The marketplace continued to describe the reward as open.

The complete timestamped response is committed as `data/audit-2026-09-11.json`. Anyone can rerun the standard-library capture script:

```bash
python scripts/capture-live-audit.py data/audit-latest.json
```

The result will naturally change as external systems change. That is a feature: RewardRadar preserves time and provenance instead of pretending that yesterday's state is permanent.

## Why ranking by payout would fail

A naive agent might sort by amount and start planning the implementation. A slightly better agent might divide payout by estimated hours. Both fail before the arithmetic begins because they trust the marketplace's state.

RewardRadar's Verifier is a separate Strands specialist with a canonical-source tool. When verification fails, it preserves the HTTP status and reason. The deterministic policy layer then refuses to treat an unverifiable or closed opportunity as actionable.

This is why the system has four roles rather than one prompt:

- Scout discovers the $1,500 row.
- Verifier discovers HTTP 410.
- Risk Analyst identifies source-integrity and payment risk.
- ROI Ranker rejects the candidate instead of letting the headline dominate.

An agent should be allowed to change its conclusion when better evidence arrives. It should not be allowed to change the evidence.

## The second trap: “open” is still not “payable”

Eight rows did survive the canonical open-state check, but that does not make their advertised total expected income. Some had many claimants. Some showed extremely large pending amounts without escrow evidence. The marketplace's own terms say that the reward creator pays after selecting a successful claimant and that the platform is not responsible if the customer does not pay.

RewardRadar therefore keeps `escrowed`, `sponsor_verified`, `acceptance_clear`, and `payout_rail_ready` as separate fields. The committed captures do not silently upgrade missing evidence to true. Deterministic code applies the disclosed multipliers, while model-generated synthesis remains subject to source-backed review.

A separate microtask marketplace made the opposite failure obvious. It had seven published tasks, but their combined displayed value was only $1.60. Those tasks may be real, yet they cannot satisfy a $100 objective. More rows are not automatically more opportunity.

## What this changes for a human

Without verification, the user can lose hours reading code, configuring a toolchain, and producing a patch for work that no longer exists. With verification, the agent spends seconds collecting the evidence and explains why it rejected the apparently best option.

That is real work for a real person. It does not replace the developer's judgment or guarantee payment. It removes repetitive cross-checking, makes risk comparable, and creates an audit trail that a human can inspect before committing time.

The human still owns eligibility, account creation, public representation, and financial details. RewardRadar never reports an advertised amount, an entry, or a possible prize as earned money. That honesty is part of the functionality, not a footer disclaimer.

## The engineering lesson

Agent demos often focus on the happy path: tool call, answer, celebration. Professional agents earn trust on the rejection path. What happens when the URL moved? When the issue is locked? When a payout depends on a sponsor who is not independently verified? When a competition requires a public social post and real capital?

RewardRadar's best output on September 11 was not a bounty. It was proof that the most tempting unclaimed row should not consume another minute.

---

Disclosure: RewardRadar and this draft were developed with substantial assistance from OpenAI Codex. The project uses the open-source Strands Agents SDK. No Amazon Bedrock or AgentCore deployment is claimed in the submitted build.
