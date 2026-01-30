# AI DevOps Commander (Monorepo)

AI-powered DevOps agent that interprets natural language, plans safe deployments, executes build/test/deploy/monitor/rollback workflows via sandboxed adapters, and surfaces status in a web dashboard.

Key stacks: Next.js + Tailwind + ShadCN (UI), FastAPI + Python (API), LangGraph (agents), Ollama/OpenAI/Gemini (LLM via provider interface), Redis + RQ (queue), SQLite→Postgres (DB), Chroma (RAG), Prometheus + Grafana (monitoring), Docker Desktop.

Monorepo layout:

```
.
├─ apps/
│  ├─ backend/        # FastAPI API, agents, orchestrator, adapters
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

## Quick start

1. Copy `.env.example` to `.env` and adjust ports/API keys.
2. Backend
   - `cd apps/backend`
   - `scripts\install.cmd`
   - `scripts\run-api.cmd` (port 3001)
   - `scripts\run-worker.cmd` (after Redis `redis-server` is up)
3. Frontend
   - From repo root: `npm install`
   - `npm run dev --workspace apps/frontend` (port 3000)

Local usage guide: see docs/LOCAL-USER-GUIDE.md for workflow plus troubleshooting.
