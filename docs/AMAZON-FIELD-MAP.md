# Amazon Devpost field map (local reference)

> This is a local completeness map. It does **not** establish the current
> state of Devpost submission `1183598`, and it does not create, edit, or send
> any entry.

This map follows the current [official rules](https://amazonappdev2026.devpost.com/rules).
It is a local completeness check, not a Devpost submission. It contains no
credentials, wallet, tax data or private account identifiers.

| Devpost field / requirement | Local evidence | Status |
|---|---|---|
| Project name | `docs/AMAZON-SUBMISSION-DRAFT.md` | Ready for owner review |
| Short description | Submission draft, README | Ready for owner review |
| Primary track | Alexa+ mapping in `docs/AMAZON-READINESS.md` | Owner must confirm |
| Mini-challenges | AWS Builder/Open Source notes and contribution draft | Owner must select only truthful claims |
| Repository URL | Feature-branch reference in `submission/DEVPOST_V0.2_UPDATE_COPY.md` | Owner must verify that the exact public branch/commit contains the reviewed MCP surface; the repository root may resolve to a different default branch |
| Open-source license | `LICENSE` | Ready; owner must verify repository displays it |
| Demo video | Checked-in `public/media/AlexaPlus-demo-v0.2.mp4` plus a separately generated, non-checked-in v0.2.1 local render | The new casefile render is local-only; owner must verify any public URL and authorize an upload or form update separately |
| Runtime proof | Self-hosted MCP endpoint and local demo | Ready locally; owner must verify public/shared judging path |
| Product feedback | `submission/AMAZON_PRODUCT_FEEDBACK.md` | Draft; owner must review before any separately authorized edit |
| Friction log | Same file; reproducible entries only | Draft; optional Stage 1 bonus |
| Open Source contribution URL | `https://github.com/cuentapraces07-ops/jhipster-control-center/pull/1` is recorded in a local draft | Owner must verify the current form state and eligibility; do not replace it with a local branch without review |
| GitHub username | None stored in this packet | Owner must enter it personally |
| AWS account / Builder ID | Not stored | Owner-controlled external gate |
| Identity and eligibility | Not inferred | Owner-controlled external gate |
| Final submission | Devpost submission `1183598` | Current state is not verified by this local audit; owner must inspect the entry before deciding whether an authorized update or submission is needed |

## Final review order

1. Verify the rules page and deadline immediately before entry.
2. Confirm the repository, license, video URL and runtime path are accessible
   to judges.
3. Replace only placeholders supported by current evidence.
4. Review the friction log and product feedback for accuracy.
5. If an update or submission is wanted, obtain a separate exact authorization
   and record the resulting URL/timestamp. Do not submit automatically.

The local preflight is `pnpm verify:amazon`; a passing result does not create
an account or imply eligibility, acceptance or payment.
