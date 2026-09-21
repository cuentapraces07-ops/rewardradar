# Amazon Build, Ship, Shape — local readiness record

This is a local engineering audit. It is not an entry, a claim of eligibility,
or a statement that Amazon has accepted the project.

## Alexa+ mapping

- The local server exposes `POST /mcp` and a `/health` endpoint.
- The JSON-RPC handshake advertises MCP protocol `2025-11-25`.
- The server exposes four explicit tools and calls them through the same
  `tools/call` boundary tested in `tests/test_alexa_mcp_server.py`.
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

The Python suite ran 33 tests; one optional SDK-dependent test was skipped.
The build completed successfully and produced the `/` and `/tv` routes.

The local transparency correction is recorded in commit `1983fd5` on the
working branch. It explicitly labels Devpost registration and final
submission as **unverified**; no entry, prize claim, or payment is represented
as complete. The public video URL was inspected separately, but no authenticated
Devpost state or public hosted app was treated as proof of eligibility.

## External gates still pending

Amazon's rules require a working project, a repository and a public demo video;
Alexa+ also requires a working Agent Skill or self-hosted MCP server, or a
clearly demonstrated simulation. The entrant must personally verify identity,
ownership/IP, eligibility, registration, final text, video visibility and any
required forms. No such external action is implied by this file.
