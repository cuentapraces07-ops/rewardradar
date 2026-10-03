# Amazon Build, Ship, Shape — local readiness record

This is a local engineering audit. It is not a claim of eligibility, selection,
payment, or current Devpost state. The local drafts below are not the
authoritative copy of any Devpost entry.

The local presentation draft is in
`docs/AMAZON-SUBMISSION-DRAFT.md`.
The local friction log draft is in
`docs/AMAZON-FRICTION-LOG.md`.
The local field-by-field map is in `docs/AMAZON-FIELD-MAP.md`.

## Alexa+ mapping

The official event page currently shows this as an online/public event due
October 23, 2026 at 12:00 PM PDT. Its Alexa+ track allows a simulated
experience in a web app. The listed Alexa+ cash tiers are $25,000 (first),
$15,000 (second), and $4,000 (third). The first-place package lists a 1:1
meeting with Amazon Developer; the owner does not permit travel, in-person
work, calls, or meetings, so an award condition requiring a meeting is out of
scope. The local planner models only the $15,000 second-place cash tier, as a
planning scenario—not a claim that the project is eligible or likely to win.
Its 1% figure is illustrative only and is not based on historical judging
data. Age/country eligibility, IP rights, final video, and registration still
require owner verification; no application has been submitted.

Sources checked 24 September 2026: [event page](https://amazonappdev2026.devpost.com/)
and [official rules](https://amazonappdev2026.devpost.com/rules).

- The local server exposes `POST /mcp` and a `/health` endpoint.
- `GET /mcp` returns `405` when no SSE stream is provided, as the 2025-11-25
  Streamable HTTP transport permits; invalid `Origin` requests receive `403`.
- The browser client advertises both JSON and SSE response formats and sends
  the negotiated `MCP-Protocol-Version` header.
- The JSON-RPC handshake advertises MCP protocol `2025-11-25`.
- The server exposes six read-only tools through the same
  `tools/call` boundary tested in `tests/test_alexa_mcp_server.py`:
  `search_rewards`, `verify_funding`, `summarize_submission_status`, and
  `plan_pursuit`, `review_pursuit_case`, and
  `respond_to_request` for bounded natural-language text requests that route
  to read-only operations without persisting the prompt.
- The implementation is fixture-only, credential-free, read-only, and never
  submits a project or configures a payout destination.
- The browser demo now makes a real local MCP initialize/notification/tool-list/
  tool-call sequence; it renders the server's structured result and fails
  visibly when the local endpoint is unavailable. Local CORS is restricted to
  the two port-5173 development origins.
- The web simulation accepts a user-written prompt, shows the deterministic
  local interpretation, supports case follow-ups, and rejects attempted
  external actions. It does not claim hosted-model or microphone speech
  recognition.
- The checked-in demo and source explain that a production deployment would
  still need an owner-controlled HTTPS host and a truthful public demo.

## Local evidence

Current local validation on 24 September 2026 included:

```text
pnpm lint
pnpm build
python -m unittest discover -s tests -v
```

In the current local worktree, the offline Python suite ran 55 tests; 54
passed and one optional SDK-dependent test was skipped. The HTTP contract tests include an
end-to-end local browser tool call, rejected-origin coverage, and the required
405 response when GET/SSE is not offered. `pnpm verify:amazon` passed all 17
local checks against the checked-in 94.89-second v0.2 demo, `pnpm lint` exited
successfully, an isolated TypeScript check passed, and `pnpm build` completed
successfully for `/` and `/tv`.

The previous v0.2.1 local renderer produced a 111.55-second H.264/AAC demo
using a real case/reconnect transcript. It predates the current natural-language
router and current opportunity fixture. A separate 115.65-second v0.3 draft
now exists at `../outputs/AlexaPlus-demo-v0.3-draft.mp4`; its key frames were
visually reviewed after correcting a text-overflow issue. It remains a local
draft, not an uploaded, linked, or public submission video. The checked-in
94.89-second v0.2 video is also historical, not current evidence.

No entry, prize claim, payment, or current Devpost state is represented as
earned or verified. This local record does not mutate any public page; the
owner must verify the current public video URL, repository branch, visibility,
and entry state immediately before any submission decision.

The repeatable local preflight is `pnpm verify:amazon`; it checks the public
repository/license reference, MCP surface, local friction log, demo duration,
submission boundary and absence of labelled live credentials. A passing
preflight is not a submission or a prize claim.

## External gates still pending

Amazon's rules require a working project, a repository and a public demo video;
Alexa+ also requires a working Agent Skill or self-hosted MCP server, or a
clearly demonstrated simulation. The entrant must personally verify identity,
ownership/IP, eligibility, registration, final text, video visibility and any
required forms. The current rules also allow a friction-log bonus of up to 10%
in Stage 1; the local draft records observations but has not been submitted.
No such external action is implied by this file.
