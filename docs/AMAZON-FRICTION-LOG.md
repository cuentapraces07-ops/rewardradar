# Amazon hackathon friction log (draft, not submitted)

Amazon's current rules say friction-log entries may receive up to a 10% bonus
during Stage 1. These entries are truthful local observations, not a claim of
Amazon support, an official bug report, or a submission. Source:
<https://amazonappdev2026.devpost.com/rules>.

## Entry 1 — credential-free local replay

- **Task:** run the self-hosted MCP demo from a clean checkout.
- **Expected:** a reviewer can exercise the Alexa+-style surface without
  configuring AWS credentials.
- **Actual:** the local fixture path runs through `python -m agent.demo` and
  `python -m agent.alexa_mcp_server`; no cloud account is required.
- **Severity:** low; this is a deliberate prototype boundary.
- **Workaround:** use the checked-in fixture and the visible disclosure; an
  owner-controlled production deployment would require HTTPS and a reviewed
  live adapter.
- **Actionable suggestion:** keep the first-run MCP quickstart credential-free
  and make the live-source boundary explicit in the CLI output.

## Entry 2 — evidence signals are easy to confuse with money

- **Task:** use an agent to rank advertised opportunities after competitor and
  CI activity changes.
- **Expected:** the voice response distinguishes pressure, delivery risk and
  acceptance gates from a verified payout.
- **Actual:** the `plan_pursuit` tool returns a bounded fixture recommendation,
  source, constraints, disclosure, and an owner-confirmation gate; it never
  turns a signal into a payout claim.
- **Severity:** important; omitting this distinction could mislead a builder.
- **Workaround:** show source, status, interpretation and the owner gate in the
  same response.
- **Actionable suggestion:** expose uncertainty as a first-class field in
  agentic interfaces instead of burying it in a long prompt.

## Entry 3 — open-source contribution proof

- **Task:** demonstrate the Open Source mini-challenge contribution.
- **Expected:** the entry can provide a repository, contribution URL, GitHub
  username and a plain-language explanation.
- **Actual:** the public repository, license, tests, demo and local evidence
  are prepared, but no new external submission or PR is claimed here.
- **Severity:** important; the contribution URL must be owner-verified before
  entry.
- **Workaround:** keep the draft fields and commit/test evidence together in
  the local submission packet.
- **Actionable suggestion:** add a preflight validator for required URLs and
  contribution metadata before the final submit control is enabled.

## Submission boundary

No friction-log entry has been sent to Amazon. The owner must verify the final
rules, eligibility, repository state and public links immediately before any
submission.
