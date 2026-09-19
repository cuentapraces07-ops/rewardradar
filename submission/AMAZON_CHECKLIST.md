# Amazon Developer Hackathon readiness

This checklist records what is evidenced locally and what still requires an
owner-controlled external action. It intentionally does not mark a prize or
payment as earned.

| Requirement | Evidence | Status |
|---|---|---|
| Alexa+ MCP server, Streamable HTTP, protocol 2025-11-25+ | `agent/alexa_mcp_server.py`, `tests/test_alexa_mcp_server.py` | Ready locally; `/health`, initialize, tools/list, tools/call smoke-tested |
| Simulated Alexa+ experience | `docs/ALEXA_PLUS.md`, structured `tools/call` responses, bounded `plan_pursuit` | Ready locally |
| Fire TV / Vega web experience | `/tv` route and `docs/FIRE_TV.md` | Ready locally; device/simulator proof pending |
| Ring API boundary | `agent/ring_adapter.py`, `docs/RING_BEE.md` | Token/device proof pending |
| Bee data boundary | `agent/bee_adapter.py`, `docs/RING_BEE.md` | Real Bee/Apple Watch export required |
| AWS Builder mini challenge | Existing Strands graph and Bedrock entry point; runtime evidence still needed | Pending evidence |
| Open Source mini challenge | Existing public repo; qualifying challenge-window contribution must be recorded | Pending window/URL |
| Public GitHub repository with open-source license | `LICENSE`, existing public RewardRadar repository | Existing; new files not uploaded |
| Demo video under three minutes, public, English | `public/media/AlexaPlus-demo-v0.2.mp4` (101.96 seconds, English, local draft) | Public upload pending |
| Product feedback for each API/SDK | Draft content can be prepared after registration | Pending |
| Explanation of changes made during window | `submission/ALEXA_PLUS_SUBMISSION.md`; v0.2.0 adds bounded `plan_pursuit` and tests | Pending timestamp/commit |
| Devpost registration | Amazon form answers prepared; required boxes and Register not clicked | **Owner confirmation required** |
| Devpost final submission | Not started | **Owner confirmation required** |

The public page currently states a deadline of **October 23, 2026 at 12:00
p.m. PDT** and says that Alexa+ entries must show the MCP server or simulated
experience working. Keep the exact deadline and requirements in the final
Devpost form as the source of truth.
