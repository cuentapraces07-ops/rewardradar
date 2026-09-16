# RewardRadar — Alexa+ track

## Project

**RewardRadar: Alexa+ Opportunity Scout** is a voice-first prototype for
screening paid technical-work listings before someone invests time. It keeps
advertised rewards, evidence gaps, estimated return, and received cash as
separate facts.

## What is implemented

The repository contains a self-hosted MCP endpoint using Streamable HTTP and
protocol `2025-11-25`, plus a dark, responsive voice-client simulation that
calls that endpoint over JSON-RPC. The transport negotiates a random
per-client session, requires the negotiated protocol header on later requests,
and rejects browser origins outside an exact local allowlist. It returns JSON
and deliberately does not offer SSE streams. The UI renders structured
responses and the call trace. It exposes three read-only tools:

1. `search_rewards` ranks a checked-in, timestamped fixture by expected hourly
   value using explicit planning assumptions.
2. `verify_funding` separates escrow, sponsor, acceptance, and payout-rail
   signals; missing evidence is not silently treated as verified.
3. `summarize_submission_status` reports the Alexa+ entry as submitted, with no
   award announced and no payment received as of September 14, 2026.

This is a working prototype of the intended voice interaction. It does not
connect to an Alexa device, present itself as a production Alexa skill, or
claim a live marketplace feed. The checked-in opportunity data is a snapshot
from September 10, 2026; estimated probabilities are not calibrated forecasts.

## Why the voice interaction matters

A short spoken question can ask the product to compress a multi-step check:
find a candidate, inspect funding evidence, and give a concise answer with the
uncertainty left intact. A user can then open the canonical source and decide
whether to proceed. The design goal is to make “not verified” and “not paid”
easy to hear—not to make a large prize headline sound certain.

## Run locally

Start the MCP fixture server:

```bash
python -m agent.alexa_mcp_server --port 8787
```

In another terminal, run the web experience:

```bash
pnpm install
pnpm dev
```

Open `http://localhost:5173` and run one of the three requests. The interface
calls the local read-only fixture endpoint at `http://127.0.0.1:8787/mcp`.
When viewing the hosted static page, the browser cannot reach a server on a
different computer; reproduce the demo locally instead.

Run the unit tests:

```bash
python -m unittest tests/test_alexa_mcp_server.py -v
```

## Honest status

The public Devpost entry is [RewardRadar: Alexa+ Opportunity Scout](https://devpost.com/software/rewardradar-alexa-opportunity-scout).
Submission is complete; award and payment are not. The video and public source
are linked from the project. No prize, Amazon endorsement, device integration,
or money earned is claimed.
