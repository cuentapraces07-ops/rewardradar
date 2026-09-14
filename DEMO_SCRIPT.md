# RewardRadar demo script — 3:35 target

## 0:00–0:20 — The problem

“A bounty feed shows advertised money. It does not show whether the issue is still open, whether ten people already claimed it, whether the funds are escrowed, or whether the payout rail works for you. RewardRadar answers the question that matters: should I spend my next hour here?”

## 0:20–0:55 — Evidence run

Open the dashboard. Point to the audit metrics: 30 advertised rows, eight canonical issues still open, one ranked pursuit, and only $1.78 across 26 rows in a separate captured microtask inventory. Explain that repository scripts collected these figures in a time-stamped September 10 snapshot and that the raw evidence is committed.

Use the dashboard replay control only to walk through that committed snapshot. State explicitly that it animates captured evidence rather than making a model request from the browser.

## 0:55–1:35 — Specialist graph

Move through Scout, Verifier, Risk, and ROI. Explain that the repository implements four Strands nodes connected through `GraphBuilder`. In the reproducible run, `DemoModel` makes one prescribed tool call per node over a checked-in fixture; that demonstrates executable orchestration and tool plumbing, not open-ended reasoning.

## 1:35–2:25 — Decision queue

Select “Godot issue #70796.” Show the locked issue, ten claimers, and low practical probability. Then select the cash hackathon. Show the cash prize, deadline, and remaining payout setup. Use the filters to isolate `pursue` and `avoid` decisions.

## 2:25–3:00 — Run it

In a terminal, run:

```bash
python -m agent.demo
```

Show the deterministic JSON ranking and four sequential Strands graph outputs. Mention that the demo needs no cloud credential, while `python -m agent.bedrock_demo` runs the same graph through Amazon Bedrock once the entrant has configured AWS access.

## 3:00–3:25 — Guardrails

Open `agent/core.py`. Explain that fixed Python formulas apply transparent risk multipliers and compute expected value from explicit inputs. Evidence fields still require review, source URLs stay visible, and an advertised amount is never reported as earned.

## 3:25–3:35 — Close

“RewardRadar does not find more work. It finds the work worth doing. Stop chasing phantom bounties.”
