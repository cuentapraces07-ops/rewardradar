# Development and reuse disclosure

RewardRadar was created during the 2026 Agents for Humans submission period.

The entrant directed development with substantial assistance from OpenAI Codex for opportunity research, product strategy, source-code generation, testing, documentation, visual design, and demo-video production. The submitted agent logic, dashboard, evidence capture, tests, architecture diagram, and video assets were produced for this project during the submission period.

The project uses standard open-source dependencies rather than copying another entrant's project or incorporating pre-existing proprietary code. Important dependencies include the Strands Agents SDK, React, Vinext/Next-compatible APIs, Tailwind CSS, Lucide icons, Pillow, edge-tts for the generated demo narration, and FFmpeg. Their respective upstream licenses continue to apply.

An optional verification module targets the MIT-licensed CALL-E Python SDK (`calle-ai==0.7.0`). It was added during the submission period from the public SDK contract, not copied from another CALL-E hackathon project. The module defaults to a redacted, network-free preview. No live phone call, CALL-E account, runtime API response, or CALL-E prize eligibility is represented by the committed demo.

The credential-free `DemoModel` is explicitly a deterministic test adapter. It is not presented as a foundation model or an AWS-hosted deployment. The static dashboard replays committed evidence and does not invoke a model. The repository now includes `agent.bedrock_demo`, an explicit Amazon Bedrock execution path that relies on the standard AWS credential chain; no completed Bedrock invocation or AgentCore deployment is claimed until corresponding runtime evidence is captured.

Three builder.aws post drafts were prepared with substantial OpenAI Codex assistance. They are source-backed drafts, not published posts. The eligible entrant must review them for accuracy before publication, and the final posts should retain an AI-assistance disclosure.

The Superteam adapter is read-only and uses public listing APIs. No Steve Agent account, X account, Solana wallet, mainnet trade, Superteam submission, or sponsor payment is claimed. The dashboard treats those unmet requirements as risk evidence rather than completed work.
