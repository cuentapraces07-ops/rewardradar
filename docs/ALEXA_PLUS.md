# Alexa+ prototype

RewardRadar includes a small self-hosted MCP endpoint for the **Alexa+** track.
It exposes a conversational interface to the same evidence-first pipeline used
by the dashboard, while keeping the demo safe and reproducible:

```bash
python -m agent.alexa_mcp_server --port 8787
```

The endpoint is `POST http://127.0.0.1:8787/mcp`; `GET /health` returns a
readiness check. It implements the minimal JSON-RPC surface a client needs:

- `initialize` advertises MCP protocol `2025-11-25` and the server identity.
- `tools/list` exposes exactly `search_rewards`, `verify_funding`,
  `summarize_submission_status`, `plan_pursuit`, and `review_pursuit_case`.
- `tools/call` returns structured JSON plus a text representation suitable for
  a voice response.

The prototype runs against `data/demo_candidates.json` only. It does not read
AWS credentials, call Amazon devices, send a phone call, bind a wallet, or
claim that a reward is guaranteed. The response explicitly labels fixture
replay and separates advertised payout from earned income. A production
deployment would use HTTPS and a reviewed live-source adapter.

`plan_pursuit` is the agentic conversation layer: it accepts a natural
constraint such as “show me a reward above $100 that fits in 40 hours,” ranks
the checked-in evidence, and opens an opaque evidence case with a short voice
summary plus safe next steps. `review_pursuit_case` can resume that case after
a new `initialize` or reconnect to the same local server process. It returns a
structured evidence card for comparison, verification gaps, or next steps.
Cases are capped, expire automatically, retain only public fixture-derived
evidence and numeric constraints, and never write to disk. Both tools are
deliberately read-only: they carry an explicit `owner_confirmation_required`
gate and never submit work, contact a sponsor, spend money, or configure a
payout destination.

## Reproduce the resumable case demo

```bash
python - <<'PY'
import json
from agent.alexa_mcp_server import handle_rpc

for request in [
    {"jsonrpc": "2.0", "id": 1, "method": "initialize"},
    {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
        "name": "search_rewards", "arguments": {"query": "", "limit": 3}
    }},
    {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
        "name": "plan_pursuit", "arguments": {"minimum_payout_usd": 100, "max_hours": 40}
    }},
]:
    print(json.dumps(handle_rpc(request), indent=2, sort_keys=True))
PY
```

Use the returned `casefile.case_id` in a later call:

```json
{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"review_pursuit_case","arguments":{"case_id":"<opaque-id>","focus":"comparison"}}}
```

## Offline protocol verification

```bash
python -m unittest tests.test_alexa_mcp_server tests.test_alexa_mcp_http -v
```

The local contract suite covers loopback `/health`, JSON-RPC
`initialize`/`tools/list`, the no-body `notifications/initialized` response,
case expiry, isolation, and a real HTTP reconnect that resumes a case. It does
not contact Amazon, Devpost, or any payment service.

This is a local build artifact pending owner confirmation for the Amazon
registration and any later public upload. It is not a claim of Amazon
endorsement, prize eligibility, or prize receipt.
