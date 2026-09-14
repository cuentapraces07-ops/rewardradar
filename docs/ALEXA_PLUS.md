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
- `tools/list` exposes `search_rewards`, `verify_funding`, and
  `summarize_submission_status`.
- `tools/call` returns structured JSON plus a text representation suitable for
  a voice response.

The prototype runs against `data/demo_candidates.json` only. It does not read
AWS credentials, call Amazon devices, send a phone call, bind a wallet, or
claim that a reward is guaranteed. The response explicitly labels fixture
replay and separates advertised payout from earned income. A production
deployment would use HTTPS and a reviewed live-source adapter.

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
