# Amazon Developer Hackathon readiness

This checklist records what is evidenced locally and what still requires an
owner-controlled external action. It intentionally does not mark a prize or
payment as earned.

| Requirement | Evidence | Status |
|---|---|---|
| Alexa+ MCP server, Streamable HTTP, protocol 2025-11-25+ | `agent/alexa_mcp_server.py`, `tests/test_alexa_mcp_server.py` | Ready locally |
| Simulated Alexa+ experience | `docs/ALEXA_PLUS.md`, structured `tools/call` responses | Ready locally |
| Fire TV / Vega web experience | `/tv` route and `docs/FIRE_TV.md` | Ready locally; device/simulator proof pending |
| Ring API boundary | `agent/ring_adapter.py`, `docs/RING_BEE.md` | Token/device proof pending |
| Bee data boundary | `agent/bee_adapter.py`, `docs/RING_BEE.md` | Real Bee/Apple Watch export required |
| AWS Builder mini challenge | Existing Strands graph and Bedrock entry point; runtime evidence still needed | Pending evidence |
| Open Source mini challenge | Existing public repo; qualifying challenge-window contribution must be recorded | Pending window/URL |
| Public GitHub repository with open-source license | `LICENSE`, existing public RewardRadar repository | Published; new files in this commit |
| Demo video under three minutes, public, English | `public/media/AlexaPlus-demo-draft.mp4` (85.3 seconds, English draft) | Published in repository; YouTube/Vimeo URL still required by final form |
| Product feedback for each API/SDK | Draft content can be prepared after registration | Pending |
| Explanation of changes made during window | `submission/ALEXA_PLUS_SUBMISSION.md`; timestamp/commit still needed | Pending |
| Devpost registration | Amazon form submitted; Devpost shows “Thanks for registering!” | Complete |
| Devpost final submission | Not started | **Owner confirmation required** |

The public page currently states a deadline of **October 23, 2026 at 12:00
p.m. PDT** and says that Alexa+ entries must show the MCP server or simulated
experience working. Keep the exact deadline and requirements in the final
Devpost form as the source of truth.
