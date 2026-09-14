# Devpost submission draft

## Project name

RewardRadar

## Tagline

Stop chasing phantom bounties.

## Track

Professional Agents

## Inspiration

Open-source contributors and independent builders see large reward totals, but those totals rarely answer the practical question: “If I start this today, what is my real chance of getting paid?” Time-stamped repository capture scripts queried public marketplaces and found closed issues, locked discussions, crowded claims, vague acceptance rules, non-escrowed rewards, and entire inventories that could not reach a $100 goal. RewardRadar was built to protect a professional’s most limited resource: focused time.

## What it does

RewardRadar is a four-specialist agent system. Scout collects current opportunities. Verifier checks the canonical issue or task. Risk Analyst flags payout, competition, scope, eligibility, and manipulation risk. ROI Ranker applies a deterministic expected-value model and issues a clear pursue, watch, or avoid verdict. The dashboard exposes every input and links back to its source.

## How we built it

The Python agent uses the Strands Agents SDK. Specialist agents are connected with `GraphBuilder` in a linear evidence pipeline. External sources are ordinary Strands tools, including public Opire, Execution Market, and Superteam adapters plus canonical GitHub and Superteam verification tools. A deterministic scoring module calculates payment probability, expected value, expected hourly return, confidence, and verdict. The interface is a responsive React/Next dashboard deployed with OpenAI Sites.

## Challenges

The largest challenge was not finding reward rows—it was resisting misleading abundance. An aggregator can say an issue is open after the underlying issue was deleted. A large pending total can come from suspicious or repeated rewards. A technically valid task can still be economically useless. We therefore kept the arithmetic and thresholds in deterministic code, retained source URLs, and made the model’s evidence inputs reviewable instead of pretending that model output is authoritative.

## Accomplishments

- A real, runnable four-node Strands graph rather than a diagram-only architecture.
- Credential-free deterministic graph demo for judges and CI.
- Conservative scoring with tests for closed items, crowding, and return per hour.
- A product decision based on time-stamped September 10 and 11, 2026 audits, with raw rows, source links, sponsor state, capital requirements, and deadline conflicts preserved.
- A time-stamped regression case in which a seemingly conventional unclaimed $1,500 reward resolved to a deleted GitHub issue (HTTP 410), while the marketplace still described it as open.
- A practical guardrail: RewardRadar prefers one qualified pursuit over a long list of distractions.

## What we learned

Opportunity discovery and opportunity verification are separate jobs. Payment probability is a product feature, not a disclaimer. The most valuable output is sometimes an evidence-backed “avoid.”

## What’s next

Add signed marketplace receipts, sponsor reputation histories, region-aware payout compatibility, GitHub App installation for higher API limits, and opt-in alerts that fire only when a reward crosses the user’s expected-value threshold.

## Built with

Python, Strands Agents SDK, `strands.multiagent.GraphBuilder`, an explicit Amazon Bedrock runner, React 19, Next/Vinext, TypeScript, Tailwind CSS, GitHub API, Opire API, Execution Market API, Superteam public APIs, and OpenAI Sites. No completed Bedrock invocation is claimed until runtime evidence is captured.

## Optional builder.aws bonus content

Three distinct English drafts are ready in `submission/`:

1. evidence-first agent architecture;
2. deterministic guardrails inside a Strands graph;
3. the deleted-$1,500 time-stamped regression case.

They must not be described as published until the eligible entrant publishes them on builder.aws and adds the resulting public URLs to Devpost.

## Links to add before final submission

- Public repository: <https://github.com/cuentapraces07-ops/rewardradar> (container exists; source push pending)
- Live demo: owner-private Sites preview plus GitHub Pages fallback; public deployment still pending
- Demo video: rendered locally under five minutes; public YouTube/Vimeo URL still required
