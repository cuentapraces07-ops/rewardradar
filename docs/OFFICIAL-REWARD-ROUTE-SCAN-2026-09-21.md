# Official reward-route scan — 2026-09-21

This is a source-checking artifact, not a claim of eligibility or expected
income. The amounts below are published maximums or prize values; none is
guaranteed, escrowed, or already awarded.

## Highest-value route currently registered: RevenueCat Shipaton 2026

Official challenge page: <https://revenuecat-shipaton-2026.devpost.com/>

A read-only check of the authenticated page on 21 September 2026 showed
**"You're registered for this hackathon"** and a deadline of **1 October 2026
at 12:45 a.m. CST**. The page advertises a **US$100,000 Grand Prize** and
additional category prizes, including US$30,000 for #BuildInPublic and
US$25,000 for OneSignal's Keep Them Coming Back Award.

The central eligibility gate is material: the project must be a brand-new
mobile app first released between 1 August and 30 September 2026 and must use
the RevenueCat SDK for at least one in-app/web purchase or RevenueCat Ads. A
normal submission needs a published App Store, Google Play, or Galaxy Store
listing, a public demo video no longer than two minutes of essential footage,
source/details, an icon, screenshots, and a free trial or promo code. The page
also lists a student-only Next Gen path with lower release friction, subject
to its eligibility rules.

The local ProofPocket work can support the evidence and monetization narrative,
but the current page does not prove that the app satisfies the release-window,
store-listing, or production-purchase gates. No store release, real purchase,
or Devpost edit was performed during this verification.

## Emergent Builder Fest — deadline passed

Official contest page: <https://emergent.sh/ai-contests/kevin-oleary-emergent-builder-fest>

The organizer's published schedule closed submissions on **20 September 2026
at 23:59 GMT**. The page says deployment is not submission: an entry needed a
separate Submitted status and confirmation email. It advertised US$50,000 for
first place, US$20,000 for second, US$10,000 for third, and smaller cash
awards through 100th place, subject to eligibility, voting, judging, and
identity/tax/banking compliance.

The authenticated Emergent page was only used for the previously authorized
prototype work; no submission was confirmed before the cutoff. Because the
deadline has passed and the rules state there is no grace period, no submission
or vote request is being attempted now. This route is closed for this cycle.

## Best fit: Amazon Build, Ship, Shape

Official rules: <https://amazonappdev2026.devpost.com/rules>

- Submission deadline: **23 October 2026 at 12:00 p.m. PDT**.
- The current local project already maps to the Alexa+ track: a self-hosted MCP
  server using MCP 2025-11-25, with a read-only evidence workflow and a local
  `/mcp` endpoint.
- Alexa+ first place is **US$25,000 cash plus US$15,000 AWS credits**; second
  place is US$15,000 cash; third is US$4,000 cash. The AWS Builder and Open
  Source mini-challenges each offer **US$5,000 cash plus US$5,000 AWS credits**.
  A project can win at most one track prize and one mini-challenge prize, so the
  maximum cash combination for the current Alexa+ route is US$30,000, not
  US$100,000.
- The Open Source mini-challenge accepts a branch, fork, or PR made during the
  hackathon window and requires contribution/repository URLs plus a description.
- The rules require a working project, public or correctly shared repository,
  sub-three-minute public demo video, product feedback, and truthful disclosure
  of third-party licenses. Existing work must be significantly updated during
  the submission period.
- Winners are subject to identity/qualification verification and required forms;
  the rules say prize delivery can take up to 60 days after completed forms.

This route is the strongest immediate engineering fit because it reuses
RewardRadar's existing local evidence and has a clear deadline. It still needs
owner-controlled review of the final submission, identity, eligibility, video,
repository visibility, and any required forms.

## Secondary low-value route: BOSS Contributor Hackathon

Official page: <https://bossconsole.ai/hackathon/>

- Submission deadline: **25 September 2026 at 11:59 p.m. IST**.
- The page advertises a **US$1,000 total cash prize pool** and accepts focused
  contributions such as a plugin, MCP connection, or developer-workflow
  improvement.
- A merged PR is explicitly **not required**; a complete, reviewable PR can be
  submitted. AI-assisted work is allowed when the contributor understands,
  reviews, and validates the result.
- The submission requires a Google sign-in and three short reflections about
  the BOSS experience. Those are owner-controlled actions, so no account,
  form, or external contribution was created.

This is a secondary route, not a substitute for the US$100,000 Shipaton target.
It is worth considering only if the owner selects a real BOSS repository and
the resulting change is independently useful and reviewable.

## High ceiling, specialist security routes

### Microsoft MSRC

Official program: <https://www.microsoft.com/en-us/msrc/bounty>

Microsoft advertises up to US$250,000 for eligible endpoint/on-premises
findings, up to US$100,000 for cloud programs, and up to US$100,000 for Zero Day
Quest. The program requires coordinated disclosure, clear reproduction, and
strict scope. It explicitly forbids accessing, modifying, or exfiltrating
customer data and disrupting services. No Microsoft system was probed and no
report was submitted.

### GitHub Bug Bounty

Official program: <https://bounty.github.com/>

GitHub advertises public-program rewards of US$10,000 or more and private-program
critical rewards of US$30,000 or more. Its safe-harbor policy requires good-faith,
in-scope research and does not authorize testing third-party services. A real,
reproducible vulnerability is required; generic scans, speculative reports, or
competitor PR activity do not qualify. No testing or submission was performed.

### Chrome Vulnerability Reward Program

Official rules: <https://bughunters.google.com/about/rules/chrome-friends/chrome-vulnerability-reward-program-rules>

The rules list high-value exploit bonuses, including up to US$250,000 for certain
full-chain demonstrations, but they also state that rewards are discretionary,
limited in number, and require a functional reproducer that Google can reproduce
and fix. Testing must be lawful and must not compromise data that is not the
researcher's own. This is not a near-term route without demonstrated security
research expertise and a fully isolated lab.

## How payout confidence is scored

Devpost's own guidance explains that most hackathons are independently organized:
the organizer, not Devpost, funds and delivers prizes. Only events marked
“Managed by Devpost” receive Devpost support for prize administration. Therefore
RewardRadar now records the organizer, management badge, rules, winner date,
verification forms, and delivery window separately from the advertised amount.

Source: <https://help.devpost.com/article/307-how-hackathons-on-devpost-work>

## Actions not taken

- No new account was created, joined, edited, submitted, or paid for during
  this scan; the existing RevenueCat registration was only read and verified.
- No security target was probed; no exploit, credential, token, wallet, or
  verification code was handled.
- No email, comment, issue, PR, or support request was sent.

## Fresh evidence from the ProofPocket workstream

The local ProofPocket prototype was revalidated after dependency hardening.
Its production dependency audit now reports no known vulnerabilities after
pinning patched `postcss`, `image-size`, and `uuid` versions. Structural
validation, TypeScript, deterministic domain tests, static security tests, and
Android/Web bundle exports all pass. This strengthens the evidence package for
the routes above, but it is not a third-party security finding, a store
release, an award, or a payment claim.

## Current official deadline recheck — 2026-09-21

Two high-value routes were rechecked against their current official pages:

- **OKX Dev Day 2026:** the builder kit still advertises a US$100,000 pool and a
  25 September 2026 23:59 UTC submission deadline, but the official terms say
  applications closed on 12 September. The builder kit is for accepted teams
  and requires a working X Layer or OKX AI integration. This route is therefore
  not treated as available unless the owner can prove prior acceptance; no
  application, Telegram join, wallet, or submission was made.
- **Amazon Build, Ship, Shape:** the official rules still show a 23 October
  2026 12:00 p.m. PDT deadline and require registration plus a working project
  in a Fire TV, Alexa+, Bee, Ring, or AWS track. The Alexa+ path specifically
  calls for an MCP following the published Model Context Protocol documentation.
  RewardRadar has a credential-free local MCP prototype and an auditable
  preflight, but no Devpost registration, AWS credit request, or submission was
  performed.

Sources: <https://www.okx.com/cs/learn/okx-dev-day-builder-kit>,
<https://www.okx.com/ru/learn/okx-dev-day-terms>, and
<https://amazonappdev2026.devpost.com/rules>.

## Newly verified high-ceiling route — CrowdStrike AI Unlocked: Agents of Chaos

Official announcement: <https://www.crowdstrike.com/en-us/press-releases/crowdstrike-announces-international-ai-security-challenge/>

Official rules: <https://www.crowdstrike.com/en-us/legal/ai-unlocked-agents-of-chaos-contest/>

- Act 3 runs through **29 September 2026 at 11:59 p.m. PT** and advertises a
  **US$70,000 grand prize**; the full three-act pool is US$100,000. However,
  the rules show that the required pre-registration window closed on 31 August
  2026, so this is actionable only if the owner already registered.
- Eligibility is restricted by country and requires age of majority, internet
  access, and a valid mailing address. Mexico is not listed in the excluded
  countries in the current rules, but the owner must verify personal
  eligibility before registering.
- Registration and MFA must be completed by the participant. The rules require
  one active account and original gameplay. Prompt injection against the game
  chatbot is allowed; bots, automated interaction, network interception,
  backend/scoring attacks, and access to other players' data are prohibited.
- Scores prioritize successful completion and token efficiency. This makes a
  careful manual run with a local, non-interacting prompt notebook a realistic
  preparation path, but no automated gameplay or external exploitation was
  performed.
- The prize is a check, delivered within 30 days after winner confirmation;
  tax documentation may be required. No registration, MFA, gameplay, or
  payment action was taken.

This is the strongest discovered route with a single prize close to the
requested target, but there is no evidence that the owner pre-registered. No
new registration should be attempted or implied. If an existing account is
confirmed, the owner can operate it manually; otherwise this route is closed
for new entrants and the offline prompt-efficiency worksheet is only reusable
for future authorized contests.

## Highest ceiling, eligibility-gated route — DARPA D2 Sprint

Official announcement: <https://www.darpa.mil/news/2026/darpa-sprint-d2>

Official competition page: <https://centralfloridatechgrove.org/darpa-d2-sprint/>

- The Documentation and Decision Support Sprint has a **US$1,000,000 total
  prize pool**, split across two lanes. Each lane lists US$300,000 for first,
  US$150,000 for second, and US$50,000 for third.
- Qualification applications are open on a rolling basis through **1 December
  2026**; final algorithm packages are due **1 March 2027**.
- The sprint is a serious medical/defense research competition involving
  tactical-casualty documentation and decision support. It requires a technical
  narrative, qualification task, isolated Docker algorithm package, and strict
  handling of government-furnished data.
- A U.S. citizen or permanent resident must apply as the team representative
  and prize recipient. Non-U.S. participants may join only through an eligible
  U.S. representative/entity; prize collection also requires a U.S. SSN or TIN.

No application, team claim, government-data download, medical advice, or
registration was made. This is a viable high-ceiling route only if the owner
can lawfully partner with an eligible U.S. representative and assemble genuine
medical/ML expertise; it must not be entered by inventing eligibility or
clinical credentials.

## Additional open route — Since AI 2026 (Finland)

Official event page: <https://sinceai2026.devpost.com/>

- The event runs **6–8 November 2026** in Turku, Finland, is free to attend,
  and accepts applicants from all countries subject to standard exceptions.
- The published prize pool is **€50,000**: a €10,000 grand prize, €2,000 for
  each of 15 company challenges, and separate €4,000/€3,000/€3,000 awards.
- Admission is reviewed on a rolling basis through the official application
  platform; a Devpost join alone does not guarantee admission.
- A working prototype must be developed substantially during the event, with
  pre-existing code and assets disclosed. The final submission needs a public
  repo, a working demo, a two-minute video, and responsible-AI notes.

This route is eligible for planning but requires travel and acceptance. No
application, travel booking, account, or submission was made.

## Small-bounty routes — verified issue state, not guaranteed payment

Official issue pages in `claude-builders-bounty/claude-builders-bounty` currently
show the following original bounty issues as **Open** and with **no branch or
pull request attached** at the time of review:

| Issue | Advertised amount | Scope | Claim path shown by the issue |
|---|---:|---|---|
| [#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1) | $50 | Structured CHANGELOG skill/script | `/opire try`, then PR, payment after merge |
| [#2](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/2) | $75 | Next.js 15 + SQLite `CLAUDE.md` | `/opire try`, then PR, payment after merge |
| [#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) | $100 | Destructive-command pre-tool hook | `/opire try`, then PR, payment after merge |
| [#4](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4) | $150 | PR-reviewing Claude Code agent | `/opire try`, then PR, payment after merge |
| [#5](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/5) | $200 | n8n + Claude weekly summary workflow | `/opire try`, then PR, payment after merge |

These are **advertised routes**, not verified receivables: the issue text says
payment is released after merge, but no merge, award, escrow balance, or
wallet transfer was independently verified. The later “claim” issue for #2
also describes a reward as **75 USDC (~$7.50 at its reference rate)**, which is
materially different from the original “$75” headline. That discrepancy is a
payment-risk flag; do not publish `/opire try`, send a wallet address, or claim
an award until the official maintainer/Opire channel confirms the exact token,
network, amount, and eligibility.

The local implementation for #1 is already available for review in the
`claude-builders-bounty-issue1` worktree. Its two unit tests pass, the Python
CLI exposes deterministic `--base`, `--output`, and `--stdout` options, and no
external claim or push has been made.

## Other official small-reward programs worth monitoring

- **Fish in a Barrel Memory Safety Bounty:** the program states rewards of
  **$100 or $500**, but only for an upstream-merged contribution that adds
  Rust/Swift bindings or migrates a qualifying security-critical component.
  The current help-wanted board lists only Linux-kernel Rust-module machinery,
  so this is a research route, not a ready-to-submit issue. Payment is arranged
  only after upstream merge and qualification review.
  Source: <https://github.com/fishinabarrel/bounty>
- **IPFS Bounties:** the official guide describes typical rewards of
  **$50–$1,000**, with eligibility after a bounty-board issue is fixed and the
  PR is merged. The repository was archived on 25 February 2026, however, and
  payouts are made by the originating party, so its board is not treated as a
  live, escrowed source until a current maintainer confirms an active issue.
  Source: <https://github.com/ipfs/devgrants/blob/main/BOUNTIES.md>
- **Project 0 infrastructure security:** the official policy lists a **$50
  minor** tier and $50–$500 medium tier, paid in USDC or equivalent. This is
  security research against active production infrastructure only; no probing,
  traffic generation, production writes, or credential use has been attempted.
  Source: <https://github.com/0dotxyz/marginfi-v2/security>

These programs are recorded as monitored opportunities, not as guaranteed
income. A route becomes actionable only after the exact issue, scope, eligibility,
payment method, and current funding are confirmed from the maintainer's source.

## Live marketplace refresh — 21 September 2026

The read-only capture at
`data/audit-2026-09-21-goal.json` queried Opire's public rewards endpoint and
then checked each referenced GitHub issue. It found **30 advertised rows**, of
which **10** resolved to canonical open issues and **20** were closed,
unverifiable, or otherwise eliminated. Among the canonical open rows priced at
or below $500 and not locked, the four visible candidates had **14, 16, 20,
and 23 claimers** respectively; one of them advertised an “auto solve hcapcha”
task and was excluded on safety grounds. The remaining open rows were either
crowded, locked, unusually inflated, or not credible as a small, low-risk
route. The live result therefore does not justify starting another marketplace
claim today.
