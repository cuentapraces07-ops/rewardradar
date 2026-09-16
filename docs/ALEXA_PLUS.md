# Alexa+ prototype

RewardRadar includes a small self-hosted MCP endpoint for the **Alexa+** track.
It exposes a conversational interface to the same evidence-first pipeline used
by the dashboard, while keeping the demo safe and reproducible:

```bash
python -m agent.alexa_mcp_server --port 8787
```

The MCP endpoint is `http://127.0.0.1:8787/mcp`; `GET /health` is a separate
readiness check. It implements the MCP `2025-11-25` Streamable HTTP lifecycle:

- `POST /mcp` accepts a single JSON-RPC message with both required response
  media types in `Accept` and `application/json` content.
- `initialize` negotiates protocol `2025-11-25`, advertises the server identity,
  and returns a cryptographically random per-client `Mcp-Session-Id`.
- Later requests require that session ID plus
  `MCP-Protocol-Version: 2025-11-25`. `DELETE /mcp` ends a session.
- `tools/list` exposes `search_rewards`, `verify_funding`, and
  `summarize_submission_status`.
- `tools/call` returns structured JSON plus a text representation suitable for
  a voice response.
- `GET /mcp` returns 405 because this prototype does not offer server-sent
  event streams. JSON responses remain valid for request/response tool calls.

The server binds to `127.0.0.1` by default and accepts browser requests only
from `http://localhost:5173` or `http://127.0.0.1:5173`. To add another exact
origin, repeat `--allow-origin https://example.com` or set
`REWARDRADAR_ALLOWED_ORIGINS` to a comma-separated list. Wildcard origins are
not allowed. This protects the local MCP endpoint from arbitrary websites; do
not bind it to a public interface without HTTPS and appropriate authentication.

The prototype runs against `data/demo_candidates.json` only. It does not read
AWS credentials, call Amazon devices, send a phone call, bind a wallet, or
claim that a reward is guaranteed. The response explicitly labels fixture
replay and separates advertised payout from earned income. A production
deployment would use HTTPS, authentication, and a reviewed live-source adapter.

## Reproduce the three-turn demo

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
]:
    print(json.dumps(handle_rpc(request), indent=2, sort_keys=True))
PY
```

The source and this draft walkthrough are published in the public repository;
the draft is not a claim of Amazon endorsement, prize eligibility, or prize
receipt. A final Devpost entry still requires the owner-controlled submission
step and any required device or hosted-runtime evidence.
