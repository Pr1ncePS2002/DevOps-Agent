# Backend (FastAPI) – Placeholder

This directory will contain the FastAPI service implementing:
- REST endpoints for command parse, plan preview, approval, execution, status
- Agents (LangGraph) for interpretation, RAG advisory, watchdog
- Orchestrator executing Git/Docker/Test/Monitor steps via adapters
- RQ workers and scheduled jobs
- Persistence (SQLite→Postgres)
- Structured logging and safety policies

Next step: scaffold FastAPI routers/services as per architecture.

## Local run (Windows cmd)

Prereqs:
- Python 3.12 (recommended) or 3.11 installed (command `python` should work)
- Note: Python 3.14 may fail dependency installs on Windows because some wheels (e.g., `pydantic-core`) are not published yet.
- Redis running at `REDIS_URL` (default: `redis://localhost:6379`)

Install deps:
```bat
cd apps\backend
scripts\install.cmd
```

Run API:
```bat
cd apps\backend
scripts\run-api.cmd
```

Run worker (separate terminal):
```bat
cd apps\backend
scripts\run-worker.cmd
```

## MVP endpoints
- GET `/health`
- POST `/projects` (create a project)
- GET `/projects` (list projects)
- POST `/commands/parse` (create a pending plan from natural language)
- POST `/executions/approve/{plan_id}` (approve + enqueue execution)
- GET `/executions/{execution_id}` (status + logs)

## Safety
- `DRY_RUN=true` by default: execution logs intended steps only.
- Real tool execution is intentionally disabled until adapters are implemented.