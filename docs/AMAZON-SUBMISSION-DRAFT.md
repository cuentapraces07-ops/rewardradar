# RewardRadar — Alexa+ local submission draft

> A Devpost read-only check on 21 September 2026 observed submission `1183598`
> as **SUBMITTED (5/5 steps done)**. This file remains a local drafting aid and
> is not authoritative over the submitted page.

This document is a truthful draft for the Amazon Build, Ship, Shape hackathon.
It is not a Devpost entry, registration, or claim of eligibility.
The field-by-field completeness map is `docs/AMAZON-FIELD-MAP.md`.

## Project

**RewardRadar: Ask once. Hear the evidence.**

RewardRadar is a read-only Alexa+-style experience for choosing work from
public opportunity evidence without confusing an advertised prize with earned
income. A user can ask for an opportunity above a minimum amount and below a
time budget; the local MCP server returns a ranked fixture-backed result,
disclosures, and owner-controlled next steps.

## Problem

Builders waste time on stale listings, locked issues, crowded claims and
unverified payout promises. Voice-first interfaces can make that worse if a
short answer hides uncertainty. RewardRadar keeps the evidence trail, risk
signals and expected-value assumptions visible in the same response.

## Alexa+ technical surface

- Self-hosted MCP endpoint: `POST /mcp` and `GET /health`.
- JSON-RPC handshake advertises MCP `2025-11-25`.
- Six read-only tools: `search_rewards`, `verify_funding`,
  `summarize_submission_status`, `summarize_evidence_signals`,
  `simulate_x402_quote`, and `plan_pursuit`. The evidence-signals tool keeps
  competitor pressure, CI failures, and acceptance gates visible without
  turning them into payout claims; `simulate_x402_quote` is a deterministic
  quote-only preview and never settles a payment.
- The demo uses checked-in fixtures only; it has no AWS credential, payout
  wallet, submission mutation, or external contact path.
- A draft friction log is prepared at `docs/AMAZON-FRICTION-LOG.md`; it is not
  submitted and contains only reproducible local observations.
- `/` presents the evidence dashboard and `/tv` presents a ten-foot view.

## Demo script (under five minutes)

1. Show the dashboard's source, payout, evidence gaps, and “not guaranteed”
   labels.
2. Open the Alexa+ replay and call `plan_pursuit` with a minimum payout and
   maximum-hours constraint.
3. Show the structured response, the voice summary, and the explicit
   `owner_confirmation_required` gate.
4. Open the source evidence panel and show that no account, wallet, or
   submission action occurred.

## Verification already run

```text
pnpm verify:amazon                                  # 9 checks passed; 94.89s demo
python -m unittest discover -s tests -p 'test_*.py'  # 47 passed, 1 skipped
pnpm lint                                             # passed
pnpm build                                            # passed; / and /tv
```

## Owner-controlled gates

Before any submission, the owner must verify the current rules, eligibility,
AWS Builder ID, public repository/license, public demo URL, final text, video
visibility, and any required account or tax information. The local artifact
does not imply that registration, prize eligibility, or payment is complete.

Source: [Amazon Developer Hackathon rules](https://amazonappdev2026.devpost.com/rules).
