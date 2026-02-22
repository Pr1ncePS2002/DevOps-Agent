# Phase 1 Review Talk Track — AI DevOps Commander

> Audience: internal review panel • Format: 10–12 minute briefing + demo preview • Visuals: [PROJECT-ABSTRACT.md](../abstract/PROJECT-ABSTRACT.md), [AI-DevOps-Commander.md](../architecture/AI-DevOps-Commander.md), [DFD PNGs](../dfd)

## 1. Opening Snapshot (0:00–0:45)
- Greet panel, restate title “AI DevOps Commander: Autonomous DevOps Agent with GitHub Actions Support”.
- Problem framing: manual DevOps runs are fragile, slow, and often bypass SOPs; goal is natural-language-driven, policy-aware automation.
- Outcome statement: system enforces plan preview + approval before any action, supports local and GitHub Actions deploys, and carries a watchdog-driven rollback safety net.

## 2. User Story & Key Capabilities (0:45–2:00)
- Walk through scenario: operator types “Deploy v1.6 to staging and run smoke tests”; interpreter builds a structured plan; reviewer approves; orchestration executes with telemetry + rollback.
- Emphasize dual deployment channels: sandboxed local adapters (Git, Docker, whitelisted scripts) and remote GitHub Actions dispatch.
- Highlight RAG + SOP compliance: LangGraph agent checks plan against vectorized SOPs in Chroma; warns or blocks if policy mismatch.

## 3. Architecture Highlight Reel (2:00–4:00)
- Reference layered diagram in [docs/architecture/AI-DevOps-Commander.md](../architecture/AI-DevOps-Commander.md).
- Call out components:
  - **Next.js UI** (App Router, Tailwind, ShadCN) for command console, plan preview, dashboards.
  - **FastAPI Gateway** exposing parse/plan/execute/status endpoints.
  - **LangGraph Agents**: CommandInterpreter, RAGAdvisor, ExecutionGraph, Watchdog.
  - **Adapters**: Git, Docker, Shell (whitelist), Prometheus, VectorStore.
  - **Persistence & Queue**: SQLite→Postgres, Redis + RQ, Chroma embeddings.
  - **Monitoring Stack**: Prometheus exporters + Grafana dashboards for latency/error budgets.
- Stress local-first design with clear scale path (SQLite→Postgres, Chroma→PGVector, Docker Desktop→Kubernetes).

## 4. Data Flow & DFD Walkthrough (4:00–5:30)
- Use Level-0 PNG to narrate high-level actors (User UI, API, Agents, Adapters, Monitoring, DB).
- Use Level-1 PNG to deepen on command lifecycle: submission → interpretation → RAG validation → plan store → approval → orchestration → watchdog + rollback.
- Tie flow steps to safety requirements: plan approval gate, structured logging with correlation IDs, constant monitoring loop.

## 5. Tooling & Technology Rationale (5:30–7:00)
- UI stack: Next.js 14 for streaming dashboards, Tailwind for quick iteration, ShadCN primitives for consistent theming.
- Backend stack: FastAPI for async-friendly APIs, LangGraph for composable agent graphs, Python ecosystem for adapters.
- Queues & storage: Redis + RQ isolate long-running deploys; SQLite baseline upgrades seamlessly to Postgres; vector memory uses Chroma now, PGVector later.
- LLM flexibility: pluggable Ollama/OpenAI/Gemini, enabling air-gapped or hosted inference.
- Monitoring & rollback: Prometheus exporters + Grafana plus WatchdogAgent enforcing MTTR targets.
- Deployment tooling: Docker Desktop/Rancher Desktop for parity with GitHub Actions workflows.

## 6. Current Progress & Evidence (7:00–8:30)
- **Frontend**: Next.js dashboard scaffolding complete (command console, plan preview, history panels) with mock data toggle — see [apps/frontend](../../apps/frontend).
- **Backend**: FastAPI skeleton, scripts (`install`, `run-api`, `run-worker`), MVP endpoint definitions, DRY_RUN safety flag — see [apps/backend](../../apps/backend).
- **Docs & Diagrams**: Comprehensive architecture narrative, DFDs, SOP/RAG flow, scaling strategy captured in `/docs`.
- **Tooling Readiness**: Redis/RQ scripts, Docker/monitoring placeholders, `.env` patterns for local spin-up.

## 7. Demo Cue (8:30–9:30)
- Show UI mock run: submit command → preview plan (from mock API) → approve to stream mock logs.
- Narrate where real backend integration slots in (API pollers hitting FastAPI, logs from Redis job).
- Optional: display DFD Level‑1 while describing each UI panel’s data source.

## 8. Roadmap & Ask (9:30–10:30)
- Near-term deliverables: finalize FastAPI routers, wire LangGraph pipeline, implement adapters + Prometheus client, integrate real data into UI, document SOP embedding pipeline.
- Risks & mitigations: LLM determinism handled via plan approval + RAG; shell access risk mitigated by sandboxed adapters; scaling handled via containerization path.
- Ask reviewers for feedback on safety controls, SOP coverage, and monitoring KPIs.

## 9. Closing & Transition to Q&A (10:30–11:00)
- Reiterate value proposition: natural-language DevOps with enforced safety and rollback guardrails.
- Invite questions, mention prepared answers in `phase1-counter-questions.md`.
