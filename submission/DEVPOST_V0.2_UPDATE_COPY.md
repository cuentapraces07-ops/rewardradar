# Devpost v0.2 update copy

Prepared for the existing **RewardRadar: Alexa+ Opportunity Scout** project.
This is copy for the owner-controlled Devpost edit; it is not an external
submission.

## Short description

An evidence-first Alexa+ MCP experience that turns a spoken payout and time
constraint into a bounded, auditable next-step plan.

## What changed in v0.2

RewardRadar exposes `plan_pursuit` alongside `search_rewards`,
`verify_funding`, `summarize_submission_status`, and `review_pursuit_case`.
A voice request such as
“show me an opportunity above $100 that fits in 40 hours” is evaluated against
the checked-in evidence fixture. The response discloses the source, constraints,
assumptions, reasons, and next steps, then stops at an explicit owner
confirmation gate. A later reconnect can review the same expiring,
memory-only evidence case without recreating its public-fixture context.

The tool is intentionally read-only: it does not submit work, contact a
sponsor, spend money, configure a payout destination, or report an advertised
reward as earned income. Invalid or unbounded voice inputs are clamped to safe
limits and a no-match result does not invent work.

## Validation

- 41 Python tests pass; one optional CALL-E SDK test is skipped (42 total)
  because that integration is not installed.
- `pnpm lint` passes.
- `pnpm build` passes for `/` and `/tv`.
- The local case workflow opens a bounded `plan_pursuit` case and resumes it
  through `review_pursuit_case` after a new initialize.
- The regenerated local v0.2.1 demo is 111.55 seconds at 1600×900, below
  three minutes, with the explicitly selected male `en-US-GuyNeural`
  narration voice. It is not uploaded or linked from this draft.

## Transparent limits

Alexa+ is simulated through a credential-free self-hosted MCP endpoint. The
fixture is not live marketplace evidence, the project does not claim an Amazon
award, and no payout has been received. Production use would require reviewed
HTTPS adapters, authentication, and owner-controlled approval before any
external action.

## Source and demo fields

- Repository: `https://github.com/cuentapraces07-ops/rewardradar`
- Video: replace the existing draft link with `https://vimeo.com/1228312635`.
- Public feature branch: `codex/alexa-plus-v0.2` (owner must verify the
  current public commit and hackathon-window timing before using this copy;
  the repository root may resolve to a different default branch).
