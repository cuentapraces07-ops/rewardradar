# RewardRadar — Alexa+ local submission draft

> This file is a local drafting aid. It does not establish the current state
> of Devpost submission `1183598` and is not authoritative over that page.

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
- Five read-only tools: `search_rewards`, `verify_funding`,
  `summarize_submission_status`, `plan_pursuit`, and `review_pursuit_case`.
  The planning tool opens an expiring, fixture-only casefile. A later review
  can compare alternatives, show verification gaps, or surface next steps
  after a reconnect to the same local server process, without turning an
  advertised prize into a payout claim.
- The demo uses checked-in fixtures only; it has no AWS credential, payout
  wallet, submission mutation, or external contact path.
- A draft friction log is prepared at `docs/AMAZON-FRICTION-LOG.md`; it is not
  submitted and contains only reproducible local observations.
- `/` presents the evidence dashboard and `/tv` presents a ten-foot view.

## Demo script (under three minutes)

1. Show the dashboard's source, payout, evidence gaps, and “not guaranteed”
   labels.
2. Open the Alexa+ replay and call `plan_pursuit` with a minimum payout and
   maximum-hours constraint.
3. Reconnect, call `review_pursuit_case`, and show the preserved alternatives,
   verification gaps, and explicit `owner_confirmation_required` gate.
4. Open the source evidence panel and show that no account, wallet, or
   submission action occurred.

## Verification already run

```text
pnpm verify:amazon                                  # 11 checks passed; 94.89s checked-in demo
python -m unittest discover -s tests -v              # 41 passed, 1 optional skip (42 total) in the current local worktree
pnpm lint                                            # passed locally
pnpm build                                           # passed locally for / and /tv
```

The v0.2.1 local casefile render is 111.55 seconds and has not been uploaded
or linked from any submission form.

## Owner-controlled gates

Before any submission, the owner must verify the current rules, eligibility,
AWS Builder ID, public repository/license, public demo URL, final text, video
visibility, and any required account or tax information. The local artifact
does not imply that registration, prize eligibility, or payment is complete.

Source: [Amazon Developer Hackathon rules](https://amazonappdev2026.devpost.com/rules).
