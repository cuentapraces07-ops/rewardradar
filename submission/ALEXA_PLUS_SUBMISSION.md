# RewardRadar — Alexa+ submission draft

## Project name

RewardRadar: the evidence-first voice for paid technical work

## One-line description

Ask Alexa+ which reward is worth your next hour; RewardRadar checks source
truth, funding signals, and competition before answering.

## Track and mini challenge

- Primary track: **Alexa+**
- Mini challenge: **AWS Builder**, only if the final build contains recorded
  AWS runtime evidence and the Devpost form confirms the selection.
- Mini challenge: **Open Source**, only if the final public repository records a
  contribution or new open-source project made during the challenge window.

## What we built

RewardRadar exposes a self-hosted MCP endpoint at `/mcp` using MCP protocol
`2025-11-25`. An Alexa+-style request can call three tools:

1. `search_rewards` ranks opportunities by payment-adjusted hourly value.
2. `verify_funding` separates escrow and sponsor evidence from an advertised
   headline amount.
3. `summarize_submission_status` reports what is registered, submitted, or
   actually paid without inventing progress.

The endpoint is backed by the same four-specialist Strands graph as the web
dashboard: Scout, Verifier, Risk Analyst, and ROI Ranker. Deterministic Python
guardrails own the arithmetic; model output cannot silently turn an unverified
reward into income.

## Why voice helps

Paid technical work is often evaluated while a builder is away from a laptop.
Alexa+ provides a natural request such as “Which opportunity is worth two hours
this weekend?” RewardRadar responds with the payout, evidence gaps, crowding,
and expected hourly value, then links the source for inspection. It is useful
because it makes uncertainty audible instead of hiding it behind a large
number.

## Safety and transparency

The demo runs on a checked-in fixture and clearly says so. It never binds a
wallet, sends a call, creates an account, or claims a prize. A production
deployment would use HTTPS, reviewed live adapters, authentication, and an
owner-controlled allowlist before connecting to Alexa+.

## Reproduction

```bash
python -m agent.alexa_mcp_server --port 8787
python -m unittest tests/test_alexa_mcp_server.py -v
```

The public repository contains the source and the English walkthrough draft.
The local run remains a prototype: it is not a claim of Amazon endorsement,
prize eligibility, or prize receipt, and final Devpost submission still needs
the owner-controlled submission step plus any required hosted/device evidence.
