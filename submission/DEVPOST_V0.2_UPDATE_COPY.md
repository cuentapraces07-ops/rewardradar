# Devpost v0.2 update copy

Prepared for the existing **RewardRadar: Alexa+ Opportunity Scout** project.
This is copy for the owner-controlled Devpost edit; it is not an external
submission.

## Short description

An evidence-first Alexa+ simulation that turns a natural-language payout and
time request into a bounded, auditable next-step plan.

## Local feature update after v0.2.1

RewardRadar adds `respond_to_request`, a deterministic local router for short
text requests, while retaining `plan_pursuit`, `review_pursuit_case`,
`search_rewards`, `verify_funding`, and
`summarize_submission_status`. A request such as
“show me an opportunity above $100 that fits in 40 hours” is evaluated against
the checked-in evidence fixture. The response discloses the source, constraints,
assumptions, reasons, and next steps, then stops at an explicit owner
confirmation gate. Follow-ups can compare alternatives, inspect evidence gaps,
check funding signals, or return next steps against the same expiring,
memory-only case without recreating its public-fixture context.

The tool is intentionally read-only: it does not submit work, contact a
sponsor, spend money, configure a payout destination, or report an advertised
reward as earned income. External-action requests are refused; request length,
payout floors, and effort limits are bounded. Raw prompt text is not retained.

The fixture closes past-deadline contest rows rather than displaying them as
active. The current Amazon Alexa+ row is a source-backed local planning case:
its 1% probability is an illustrative scenario only, and the $15,000 amount is
the listed second-place cash tier. No entry, owner eligibility, or prize is
claimed. The first-place bundle lists a meeting, which is outside the owner's
allowed scope; do not accept an award condition requiring a meeting.

## Validation

- 54 Python tests pass; one optional CALL-E SDK test is skipped (55 total)
  because that integration is not installed.
- `pnpm lint` passes.
- `pnpm build` passes for `/` and `/tv`.
- Offline tests exercise natural request parsing, case follow-ups, funding
  checks, blocked external-action prompts, and the HTTP/MCP boundary.
- The prior 111.55-second local video predates the interactive text router.
  A separate 115.65-second v0.3 draft now demonstrates the updated flow and
  remains local; it has not been uploaded or linked to a public entry. The
  owner should review the full video and all contest-required identity, rights,
  eligibility, and submission fields before deciding whether to use it.

## Transparent limits

Alexa+ is simulated through a credential-free self-hosted MCP endpoint. The
router is deterministic Python code, not a hosted LLM or speech recognizer.
The fixture is not live marketplace evidence, the project does not claim an
Amazon award, and no payout has been received. Production use would require
reviewed HTTPS adapters, authentication, and owner-controlled approval before
any external action.

## Source and demo fields

- Repository: `https://github.com/cuentapraces07-ops/rewardradar`
- Video: replace the existing draft link with `https://vimeo.com/1228312635`.
- Public feature branch: `codex/alexa-plus-v0.2` (owner must verify the
  current public commit and hackathon-window timing before using this copy;
  the repository root may resolve to a different default branch).
