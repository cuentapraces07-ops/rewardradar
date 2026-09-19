# Amazon product feedback draft

This is owner-reviewed copy for the Amazon Developer Hackathon submission. It
is not a published response until the owner confirms the final Devpost edit.

## Tools used

- **Alexa+ / MCP:** a self-hosted Streamable HTTP endpoint implementing MCP
  `2025-11-25`. The checked-in server exposes `search_rewards`,
  `verify_funding`, `summarize_submission_status`, and the bounded,
  read-only `plan_pursuit` tool.
- **Strands Agents SDK:** the dashboard's four-node decision engine uses a
  deterministic adapter for reproducible local evidence. The Bedrock entry
  point is included, but no live Bedrock invocation is claimed in the
  credential-free demo.
- **Amazon Devpost submission:** the web replay is an Alexa+-style simulation
  permitted by the track rules. It shows the same request/response boundary
  and the explicit owner-confirmation gate.

## What worked well

The MCP surface was straightforward to keep inspectable: protocol discovery,
tool schemas, bounded inputs, source-backed results, and refusal paths are all
covered by local tests. The simulation made it possible to demonstrate the
voice interaction without pretending that a device connection or payout had
occurred. The static dashboard loads quickly and keeps evidence, uncertainty,
and effort visible beside the headline amount.

## What needs work

The onboarding documentation should make the distinction between a simulated
Alexa+ client and a live Alexa+ integration more prominent. A production
deployment also needs reviewed HTTPS hosting, authentication, replay-safe
request IDs, and a small owner-controlled approval service before any external
submission or financial action. The demo intentionally does not call a live
marketplace or configure a payout rail.

## Onboarding experience

From a clean checkout, install the Python demo dependencies, run the unit
tests, start the local web app, and open `/`. The repository includes the
MCP server smoke path and a generated sub-three-minute demo video. No cloud
credentials are required for the reproducible fixture path.

## Would we build with these tools again?

**Yes.** MCP provided a small, auditable contract for a voice-first tool
surface, while Strands made the specialist hand-offs explicit. We would use
the same stack again for a production pilot after the hosting, auth, and
approval boundaries above were reviewed.

## Friction log

| Task | Expected | Actual | Severity | Workaround | Suggestion |
| --- | --- | --- | --- | --- | --- |
| Build a voice-first prototype without cloud credentials | A local MCP replay should be enough to demonstrate the contract | The track permits a simulation, but the distinction is easy to miss in the submission form | Medium | Added a four-turn replay, fixture badge, and explicit disclosure | Add a submission-form hint for simulated Alexa+ projects |
| Show safe agentic planning | A tool call should be bounded and reviewable | Unbounded “do it” language can imply external action | Medium | Added `plan_pursuit` bounds and an owner-confirmation gate | Document the recommended confirmation pattern in the MCP examples |
