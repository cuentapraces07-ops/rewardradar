# Amazon Developer Hackathon — Alexa+ entry status

This checklist reports the Alexa+ track only. It separates completed entry
work from prize and payment outcomes; a public submission is not an award.

| Requirement / state | Evidence | Status |
|---|---|---|
| Alexa+ entry | [Public Devpost project](https://devpost.com/software/rewardradar-alexa-opportunity-scout) | Submitted Sep 14, 2026 |
| Public source and license | [RewardRadar repository](https://github.com/cuentapraces07-ops/rewardradar), `LICENSE` | Public; MIT |
| Working demonstration | `app/alexa/page.tsx` calls the local `agent/alexa_mcp_server.py` over JSON-RPC | Local fixture demo; no Alexa device or production skill connection claimed |
| MCP tools | `search_rewards`, `verify_funding`, `summarize_submission_status` | Read-only; covered by unit tests |
| Market freshness | `data/demo_candidates.json`, collected Sep 10, 2026 | Historical fixture, not a live listing feed |
| Video | [Public Vimeo walkthrough](https://vimeo.com/1226715422) | Current version; English narration, under three minutes |
| Award / cash | Devpost result not yet announced | No prize awarded; no payment received as of Sep 14, 2026 |

The MCP demo is a prototype, not an Amazon product integration. Funding fields
and estimated probabilities in its checked-in fixture are planning evidence,
not proof of escrow, eligibility, acceptance, or future payment. No cash is
recorded as earned until funds are received.
