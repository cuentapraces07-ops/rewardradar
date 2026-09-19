# RewardRadar Alexa+ v0.2 verification packet

Recorded locally on 2026-09-19 (America/Mexico_City). This packet documents a
credential-free fixture run. It is evidence for review, not a claim that a
live Alexa device, a live payout, or a prize has been obtained.

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
Ran 33 tests in 0.035s
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

The v0.2 video is now publicly uploaded at
https://vimeo.com/1228312635. The existing Devpost entry remains submitted,
but its video field still points at the older upload. No new final submission,
account change, maintainer message, or payout action is claimed by this packet.
