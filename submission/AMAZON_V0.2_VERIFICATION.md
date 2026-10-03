# RewardRadar Alexa+ v0.2 verification packet

Historical record from 2026-09-19 (America/Mexico_City). This packet documents
a credential-free fixture run from that date. It is evidence for review, not a
claim that a live Alexa device, a live payout, or a prize has been obtained.

## What changed

- Added the read-only `plan_pursuit` MCP tool.
- Inputs are bounded (`max_hours` is clamped to 0.5–168 and the payout floor is
  bounded); invalid values fail closed.
- The result includes the source-backed match, assumptions, next step, and an
  explicit `owner_confirmation_required` gate.
- The tool cannot submit work, contact a maintainer, spend money, configure a
  payout rail, or report a payment as guaranteed.
- The Alexa+ demo now shows the plan step and the safety gate in a 94.89-second
  local MP4, below the three-minute submission limit, with the explicitly
  selected male `en-US-GuyNeural` narration voice.

## Reproduction

```text
python -m unittest discover -s tests -v
Ran 38 tests in that historical verification pass; one optional SDK test skipped.
OK (skipped=1)

python -m compileall -q agent tests scripts
PASS

pnpm lint
PASS

pnpm run build:pages
PASS — static routes `/` and `/tv` prerendered

pnpm build
PASS — vinext client, RSC, and SSR environments built

python scripts/make-alexa-plus-video.py outputs/AlexaPlus-demo-v0.2-local.mp4
outputs/AlexaPlus-demo-v0.2-local.mp4

ffprobe ... outputs/AlexaPlus-demo-v0.2-local.mp4
 duration=94.894467
codec=h264/aac; resolution=1600x900; fps=29.99
```

The one skipped test is the optional CALL-E SDK integration test; it is not
needed for the credential-free Alexa+ prototype path.

## Submission boundary

This historical local record references the v0.2 Vimeo URL
https://vimeo.com/1228312635. Current public accessibility and any Devpost
linkage require owner verification. The local submission packet is prepared,
but Devpost registration and final submission remain owner-controlled and are
not verified here. No account change, maintainer message, or payout action is
claimed by this packet.

## Fresh local verification — 2026-09-23 America/Mexico_City

The current checkout was revalidated without changing any external account:

```text
python -m unittest discover -s tests -v
41 passed, 1 optional skip (42 total), OK

pnpm run verify:amazon
11 checks passed, 0 failed; checked-in demo 94.89s

pnpm lint
PASS

pnpm build
PASS — local build completed for `/` and `/tv`
```

The same local validation separately generated a non-checked-in v0.2.1 local
render from a real `plan_pursuit`/`review_pursuit_case` transcript. `ffprobe`
reports H.264/AAC, 1600×900, and 111.55 seconds. The artifact remains local
and has not been uploaded or linked from a Devpost entry.

This confirms the local Alexa+ evidence packet remains reproducible. It does
not prove a live Alexa+ account, a submitted Devpost entry, eligibility, a
winner decision, or a payout.
