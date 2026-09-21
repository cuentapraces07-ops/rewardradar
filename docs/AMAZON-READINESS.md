# Amazon Build, Ship, Shape — local readiness record

This is a local engineering audit. It is not a claim of eligibility, selection,
or payment. A read-only check on 21 September 2026 observed the authenticated
Devpost submission `1183598` as **SUBMITTED (5/5 steps done)** and the public
project page as associated with the Amazon hackathon; the local drafts below
are not the authoritative copy of that submission.

The local presentation draft is in
`docs/AMAZON-SUBMISSION-DRAFT.md`.
The local friction log draft is in
`docs/AMAZON-FRICTION-LOG.md`.
The local field-by-field map is in `docs/AMAZON-FIELD-MAP.md`.

## Alexa+ mapping

- The local server exposes `POST /mcp` and a `/health` endpoint.
- The JSON-RPC handshake advertises MCP protocol `2025-11-25`.
- The server exposes six explicit tools, including the read-only
  `summarize_evidence_signals` ledger and the quote-only
  `simulate_x402_quote` preview; all are called through the same `tools/call`
  boundary tested in `tests/test_alexa_mcp_server.py`.
- The implementation is fixture-only, credential-free, read-only, and never
  submits a project or configures a payout destination.
- The checked-in demo and source explain that a production deployment would
  still need an owner-controlled HTTPS host and a truthful public demo.

## Local evidence

The following checks passed on 21 September 2026:

```text
pnpm lint
pnpm build
python -m unittest discover -s tests -v
```

The Python suite ran 47 tests; one optional SDK-dependent test was skipped.
The build completed successfully and produced the `/` and `/tv` routes.

The local transparency correction is recorded in commit `1983fd5` on the
working branch. It labels the local draft as unsubmitted; the later authenticated
Devpost observation is recorded separately in `submission/AMAZON_CHECKLIST.md`.
No entry, prize claim, or payment is represented as earned. The submitted page
currently points to Vimeo `1226715422`, while the latest local demo is
`1228312635`; no external edit was made.

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
