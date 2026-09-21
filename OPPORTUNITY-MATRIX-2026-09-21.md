# Opportunity matrix — 2026-09-21

This is a research artifact, not a submission or a promise of payment. Every
amount below is an advertised prize pool from the linked official source. A
prize becomes payable only after the entrant satisfies the rules, is selected,
and completes any identity or payout verification required by the organizer.

## Ranked opportunities

| Priority | Opportunity | Official deadline / prize signal | Fit with current work | Blocking gate |
| --- | --- | --- | --- | --- |
| 1 | [RevenueCat Shipaton 2026](https://revenuecat-shipaton-2026.devpost.com/rules) | Sep 30, 2026 11:45pm PDT; official rules list a US$100,000 Grand Prize plus multiple US$20,000 category first prizes | ProofPocket already has a local Android prototype, a verified 1179×2556 screenshot, a paywall concept, and a successful public CI run | A qualifying first public store release, RevenueCat premium access/test path, public ≤2-minute video, submission fields, and owner eligibility/identity review |
| 2 | [CLOCK IN: Solana Mobile Hackathon](https://solanamobile.com/blog/clock-in-the-solana-mobile-hackathon) | Submissions close Oct 8, 2026; includes a US$10,000 SKR integration prize plus a broader pool | ProofPocket's Android direction and existing Solana/x402 work provide a credible starting point | Functional APK, GitHub repo, demo video, pitch deck, and eventual dApp Store publication to claim a prize; exact pool and eligibility must be checked before entry |
| 3 | [LexHack 2026](https://lexhack-2026.devpost.com/rules) | Sep 27, 2026 5:00pm EDT; Devpost advertises US$74,248 cash | High headline value and global online format | Official rules require student status and one team/project; do not enter unless the owner confirms eligibility |
| 4 | [Ready, Set...ID the Biothreat Challenge](https://www.app.cloud.gov/challenges/ready-set-id-biothreat) | Oct 14, 2026 noon ET; official listing advertises US$999,990 total | Potentially high value, but it is a specialized federal algorithmic challenge rather than a quick software bounty | Full rules, eligibility, data-use constraints, and scientific capability need primary-source review before any work; no bio/security claims are being made |
| Watch | [InfinityX Global Hackathon 2K26](https://infinityx-2k26.devpost.com/rules) | Sep 25, 2026 11:45pm IST; global eligibility is stated | Could accept an existing prototype if the rules permit it | The rules page did not expose a verified prize amount in the current scan; do not prioritize until the official sponsor/prize page is verified |

## Why Shipaton is the immediate engineering target

The official rules list a US$100,000 Grand Prize, but that amount is a prize,
not guaranteed income. They require a working mobile application using RevenueCat, a
first public release during the submission period, a demo video, a 1024×1024
icon, a 1179×2556 screenshot without a device frame, and either a free trial or
a promo code for judges. ProofPocket now has the local evidence and CI pieces,
but it does **not** yet have a store release or a judge-access path. Those are
owner-controlled gates, not facts to invent in a submission.

ProofPocket's strongest truthful category hypotheses are the Peace Prize (social
good) and HAMM (responsible monetization). The Grand Prize is a stretch target
because the rules weigh launch momentum and growth; no traction is claimed.

## Execution discipline

1. Build and test locally first; keep commit hashes, test output, and artifact
   digests in the evidence packet.
2. Never claim a store release, user traction, winner status, or payment before
   the official platform confirms it.
3. Keep the submission, identity, tax, KYC, store, and payout decisions with
   the owner; no account or payment configuration is performed by this matrix.
4. Prefer one complete, rule-compliant Shipaton entry over many incomplete
   applications. Re-evaluate the ranking whenever an official rule or deadline
   changes.

## Current status

- RewardRadar's deterministic audit and 33-test suite pass locally.
- ProofPocket's `bc16c7b` public CI run succeeded and produced an unsigned
  artifact; this is not a store release.
- No opportunity in this file has been submitted, and no prize is verified.
