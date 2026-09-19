# Devpost v0.2 update copy

Prepared for the existing **RewardRadar: Alexa+ Opportunity Scout** project.
This is copy for the owner-controlled Devpost edit; it is not an external
submission.

## Short description

An evidence-first Alexa+ MCP experience that turns a spoken payout and time
constraint into a bounded, auditable next-step plan.

## What changed in v0.2

RewardRadar now exposes `plan_pursuit` alongside `search_rewards`,
`verify_funding`, and `summarize_submission_status`. A voice request such as
“show me an opportunity above $100 that fits in 40 hours” is evaluated against
the checked-in evidence fixture. The response discloses the source, constraints,
assumptions, reasons, and next steps, then stops at an explicit owner
confirmation gate.

The tool is intentionally read-only: it does not submit work, contact a
sponsor, spend money, configure a payout destination, or report an advertised
reward as earned income. Invalid or unbounded voice inputs are clamped to safe
limits and a no-match result does not invent work.

## Validation

- 33 Python tests pass; one optional CALL-E SDK test is skipped because that
  integration is not installed.
- `pnpm lint` passes.
- Next static build passes for `/` and `/tv`.
- Vinext client, RSC, and SSR build passes.
- The local replay exposes four voice turns, including the bounded
  `plan_pursuit` owner-confirmation step.
- The English local demo is 94.89 seconds at 1600×900, below three minutes,
  with the explicitly selected male `en-US-GuyNeural` narration voice.

## Transparent limits

Alexa+ is simulated through a credential-free self-hosted MCP endpoint. The
fixture is not live marketplace evidence, the project does not claim an Amazon
award, and no payout has been received. Production use would require reviewed
HTTPS adapters, authentication, and owner-controlled approval before any
external action.

## Source and demo fields

- Repository: `https://github.com/cuentapraces07-ops/rewardradar`
- Video: replace the existing draft link with `https://vimeo.com/1228312635`.
- Public repository commit: `3e336a9a90b79c79ec5142983d42f66eefa2bc50`
