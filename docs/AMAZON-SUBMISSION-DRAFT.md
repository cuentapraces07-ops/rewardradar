# RewardRadar — Alexa+ local submission draft

> This file is a local drafting aid. It does not establish the current state
> of Devpost submission `1183598` and is not authoritative over that page.

This document is a truthful draft for the Amazon Build, Ship, Shape hackathon.
It is not a Devpost entry, registration, or claim of eligibility.
The field-by-field completeness map is `docs/AMAZON-FIELD-MAP.md`.

## Project

**RewardRadar: Evidence before effort.**

RewardRadar is a read-only Alexa+ web simulation for evaluating public work
opportunities without confusing an advertised prize with earned income. A user
types a payout floor and time budget; a local self-hosted MCP server routes the
request, checks a disclosed fixture, and returns a ranked result, assumptions,
evidence gaps, and owner-controlled next steps. The demo does not use speech
recognition, a hosted language model, or live marketplace data.

## Problem

Builders waste time on stale listings, locked issues, crowded claims and
unverified payout promises. A conversational interface can make that worse if
a short answer hides uncertainty. RewardRadar keeps the source trail, risk
signals and illustrative planning assumptions visible in the same response.

## Alexa+ technical surface

- Self-hosted MCP endpoint: `POST /mcp` and `GET /health`.
- JSON-RPC handshake advertises MCP `2025-11-25`.
- Six read-only tools: `search_rewards`, `verify_funding`,
  `summarize_submission_status`, `plan_pursuit`, `review_pursuit_case`, and
  `respond_to_request`. The last is a deterministic text router, not an LLM.
  Planning opens an expiring, fixture-only casefile; a later request can
  compare alternatives, check funding signals, show verification gaps, or
  surface next steps after reconnecting to the same local server process.
- The Amazon Alexa+ row uses the advertised second-place cash amount and a 1%
  illustrative scenario input only. That percentage is not an empirical win
  rate; escrow and payout-rail readiness are not verified. The prototype never
  turns an advertised prize into earned income or a payment guarantee.
- The demo uses checked-in fixtures only; it has no AWS credential, payout
  wallet, submission mutation, or external contact path.
- A draft friction log is prepared at `docs/AMAZON-FRICTION-LOG.md`; it is not
  submitted and contains only reproducible local observations.
- `/` presents the evidence dashboard and `/tv` presents a ten-foot view.

## Intended demo capture (under three minutes; runtime capture still pending)

1. Start `pnpm dev` and `python -m agent.alexa_mcp_server --port 8787` locally.
2. Record the browser UI while typing “Find an opportunity above $100 for 40
   hours” and showing the response returned by the real local MCP endpoint.
3. Reconnect and show a follow-up against the same in-memory case, including
   the funding check and explicit `owner_confirmation_required` gate.
4. Show the source evidence and that no account, wallet, or submission action
   occurred.

The local v0.3 MP4 is a narrated storyboard built from real local tool
responses, not a screen recording of the browser UI. It is useful for review
but is not sufficient evidence by itself for the contest's demo-video
requirement. Do not describe it as a live device or browser capture.

## Verification already run

```text
pnpm verify:amazon                                  # 17 checks passed; checked-in v0.2 asset is 94.89s
python -m unittest discover -s tests -v              # 54 passed, 1 optional skip (55 total)
pnpm lint                                            # passed locally
```

The current local v0.3 storyboard at
`../outputs/AlexaPlus-demo-v0.3-validated.mp4` is 115.56 seconds, H.264/AAC,
1600×900. It has not been uploaded or linked from any submission form, and it
does not replace the separate runtime-capture step above. The checked-in 94.89s
v0.2 video and the older 111.55s v0.2.1 render predate the typed router.

## Owner-controlled gates

Before any submission, the owner must verify the current rules, eligibility,
AWS Builder ID, public repository/license, public demo URL, final text, video
visibility, and any required account or tax information. The local artifact
does not imply that registration, prize eligibility, or payment is complete.

Source: [Amazon Developer Hackathon rules](https://amazonappdev2026.devpost.com/rules).
