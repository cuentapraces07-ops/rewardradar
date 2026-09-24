# Alexa+ prototype

RewardRadar includes a small self-hosted MCP endpoint for the **Alexa+** track.
It exposes a conversational interface to the same evidence-first pipeline used
by the dashboard, while keeping the demo safe and reproducible:

```bash
python -m agent.alexa_mcp_server --port 8787
```

For the browser simulation, run the two local processes in separate terminals:

```bash
# terminal 1, from the repository root
pnpm dev

# terminal 2, from the repository root
python -m agent.alexa_mcp_server --port 8787
```

Open `http://127.0.0.1:5173`, enter a short request such as
`Find an opportunity above $100 for 40 hours`, and select
**Ask RewardRadar**. The browser performs the MCP
initialize/initialized/tools-list/tools-call sequence against the local
server, then renders the actual structured result and session identifier.
Follow-up buttons compare alternatives, show evidence gaps, or reveal next
steps for the same short-lived case. The HTTP server permits browser CORS only from the two local
development origins on port 5173; it binds to loopback by default and has no
credentials or external-data actions. If the endpoint is unavailable, the UI
shows the connection failure rather than substituting a prerecorded answer.

The MCP endpoint is `http://127.0.0.1:8787/mcp`; `GET /health` returns a
readiness check and `GET /mcp` returns `405 Method Not Allowed` because the
prototype does not offer an SSE stream. The browser client lists both JSON and
SSE in `Accept` and sends `MCP-Protocol-Version: 2025-11-25` on its requests.
The server rejects disallowed `Origin` values with `403`, including direct
POSTs, and allows CORS only from the two local development origins. It
implements the minimal JSON-RPC surface a client needs:

- `initialize` advertises MCP protocol `2025-11-25` and the server identity.
- `tools/list` exposes `search_rewards`, `verify_funding`,
  `summarize_submission_status`, `plan_pursuit`, `review_pursuit_case`,
  and `respond_to_request`.
- `tools/call` returns structured JSON plus a text summary suitable for the
  browser's Alexa+ simulation. The browser accepts typed text; it does not
  provide speech recognition.

The prototype runs against `data/demo_candidates.json` only. Expired contest
rows are explicitly closed, the prior microtask inventory is snapshot-only,
and the current Amazon row is still only a checked-in fixture. Its 1% figure
is an illustrative scenario, not an observed prize probability; the cash
amount used in the plan is the second-place tier, and the owner's no-meeting
constraint excludes accepting any award condition that requires a meeting.
No eligibility or submission is confirmed. It does not read
AWS credentials, call Amazon devices, send a phone call, bind a wallet, or
claim that a reward is guaranteed. The response explicitly labels fixture
replay and separates advertised payout from earned income. A production
deployment would use HTTPS and a reviewed live-source adapter.

The request router is deterministic Python code, not a hosted LLM or
speech recognizer. It accepts typed text in the web simulation and refuses
requests to submit, contact, publish, create accounts, or move money. The
browser sends prompt text only to the local MCP endpoint.

`respond_to_request` deterministically parses a short natural-language request
and routes it to a fixture-backed pursuit plan, a truthful submission-status
summary, or a follow-up review. For example, “show me an opportunity above $100 that
fits in 40 hours” becomes an explicit payout floor and effort ceiling;
`review_pursuit_case` can compare alternatives, show evidence gaps, or return
next steps after a new `initialize` or reconnect to the same local server
process. The prompt text is not stored; the short-lived case retains only
parsed numeric constraints and public fixture evidence.
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

The official [Amazon event page](https://amazonappdev2026.devpost.com/) lists
the Alexa+ track, permits a simulated experience in a web app, and gives an
October 23, 2026 deadline. This is still only a local build artifact: no
registration or entry is claimed. The first-place bundle lists a meeting;
the owner has ruled out meetings, travel, and calls, so no award condition
requiring one may be accepted. This is not a claim of Amazon endorsement,
prize eligibility, or prize receipt.
