# AI DevOps Commander (Monorepo)

AI-powered DevOps agent that interprets natural language, plans safe deployments, executes build/test/deploy/monitor/rollback workflows via sandboxed adapters, and surfaces status in a web dashboard.

Key stacks: Next.js + Tailwind + ShadCN (UI), NestJS + TypeScript (API), LangGraph (agents), Ollama (local LLM), Redis + BullMQ (queue), SQLite→Postgres (DB), Chroma (RAG), Prometheus + Grafana (monitoring), Docker Desktop.

Monorepo layout:

```
.
├─ apps/
│  ├─ backend/        # NestJS API, agents, orchestrator, adapters
│  └─ frontend/       # Next.js UI for commands, plan preview, dashboards
├─ packages/
│  └─ shared/         # Shared TypeScript types and utilities (DTOs, schemas)
├─ infra/
│  ├─ scripts/        # Whitelisted scripts for ShellAdapter
│  ├─ monitoring/     # Prometheus/Grafana notes and configs (later)
│  ├─ docker/         # Dockerfiles, compose (later)
│  └─ db/             # DB migrations/configs (later)
└─ docs/
   └─ architecture/   # Architecture docs and diagrams
```

Getting started (skeleton only): see docs/architecture/AI-DevOps-Commander.md for design. Implementation scaffolding comes next.
