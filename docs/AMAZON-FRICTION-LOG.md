# Amazon hackathon friction log: Alexa+ MCP session isolation

This entry describes an implementation issue found in RewardRadar's own
self-hosted MCP prototype and reproduced with local loopback HTTP tests. It is
not a report that an Amazon service failed, and it does not imply Amazon
reviewed or endorsed the project. No Amazon service, account, or credentials
were used to reproduce it.

The hackathon rules say friction-log entries may receive up to a 10% bonus in
Stage 1 judging. This is a possible score adjustment, not a guaranteed bonus,
award, or payment. Source:
<https://amazonappdev2026.devpost.com/rules>.

## Entry 1 — isolating Streamable HTTP MCP sessions

- **Task:** implement the Alexa+ track's self-hosted MCP endpoint using
  Streamable HTTP and protocol version `2025-11-25`.
- **Steps:** send two independent `initialize` requests, then send each
  client's follow-up requests using the returned session ID; exercise the
  handshake, initialized notification, tools, and session expiry in the
  loopback HTTP suite.
- **Expected:** each initialized session can be identified and managed
  independently. The MCP transport specification says a session ID should be
  globally unique and cryptographically secure.
- **Actual:** the first server implementation used one process-wide session ID
  for every client. We changed it to create a cryptographically random ID per
  initialization and track protocol version, initialization state, and idle
  expiry per session.
- **Severity:** medium — clients could not be represented as distinct
  protocol sessions, so session lifecycle and isolation were not modeled
  correctly.
- **Workaround:** maintain a per-initialization session record with a bounded
  idle lifetime, require the negotiated protocol header on follow-up requests,
  and cover independent clients and expiry with loopback tests.
- **Actionable suggestion:** publish a compact Alexa+-oriented MCP example or
  checklist covering independent initialization, session-ID uniqueness,
  required headers, and reconnect behavior.

## Evidence and scope

- The initial behavior and corrective change are visible in commit
  [`71c573d`](https://github.com/cuentapraces07-ops/rewardradar/commit/71c573d).
- Current coverage is in
  [`tests/test_alexa_mcp_http.py`](https://github.com/cuentapraces07-ops/rewardradar/blob/codex/amazon-preflight-v0.2.1/tests/test_alexa_mcp_http.py).
- The protocol reference is the [MCP Streamable HTTP specification for
  `2025-11-25`](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports).
