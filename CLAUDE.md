# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI DevOps Commander** — A monorepo with a Next.js frontend and FastAPI backend that lets users deploy projects via natural language commands. Commands are parsed (LLM or regex fallback), validated against SOPs via RAG, previewed for approval, then executed through Docker.

## Repository Structure

```
apps/
  frontend/          # Next.js 14 dashboard (port 3000)
  backend/           # FastAPI server (port 3001) + RQ worker
packages/
  shared/            # TypeScript DTOs shared between frontend and backend
infra/               # Whitelisted scripts, Dockerfile templates, monitoring placeholders
```

## Commands

### Backend (from `apps/backend/`)

```bash
scripts\install.cmd          # One-time: create .venv and install Python deps
scripts\run-api.cmd          # Start FastAPI server (port 3001)
scripts\run-worker.cmd       # Start RQ background worker
scripts\run-redis.cmd        # Start Redis via Docker
scripts\check-redis.cmd      # Check Redis connectivity

# Tests
.venv\Scripts\python.exe -m pytest tests/                                  # All tests
.venv\Scripts\python.exe -m pytest tests/test_command_interpreter.py       # Single file
```

### Frontend (from repo root)

```bash
npm install
npm run dev --workspace apps/frontend        # Dev server (port 3000)
npm run build --workspace apps/frontend      # Production build
npm run test --workspace apps/frontend       # Vitest tests
npm run lint --workspace apps/frontend       # ESLint
```

### Local Stack

```bash
# Terminal 1
docker run --name redis -p 6379:6379 -d redis:7

# Terminal 2 (API)
cd apps/backend && scripts\run-api.cmd

# Terminal 3 (worker)
cd apps/backend && scripts\run-worker.cmd

# Terminal 4 (frontend)
npm run dev --workspace apps/frontend
```

## Architecture

### Request Flow

```
Natural language command
  → CommandInterpreter (LLM via factory, or deterministic regex fallback)
  → RAGAdvisor (validates against project SOPs stored in Chroma)
  → Plan preview returned to user (approval required)
  → Orchestrator: validate → docker build → docker run → health check → register
  → Watchdog monitors container; auto-rollbacks on failure
```

### Backend Services (`apps/backend/app/services/`)

| File | Role |
|---|---|
| `command_interpreter.py` | Parses commands; LLM primary, regex fallback |
| `orchestrator.py` | Executes approved deployment plans step-by-step |
| `rag_advisor.py` | Chroma-based SOP validation before execution |
| `watchdog.py` | Polls container health; triggers rollback if unhealthy |
| `project_analysis.py` | Detects tech stack; auto-generates Dockerfiles |
| `project_registration.py` | Onboards local paths or GitHub repos |
| `llm/factory.py` | Selects LLM client based on `LLM_PROVIDER` env var |

### API Routes (`apps/backend/app/api/routes/`)

`projects` · `commands` · `executions` · `providers` · `deploy_status` · `demo`

### Frontend Key Files

| File | Role |
|---|---|
| `lib/api.ts` | All backend API calls |
| `lib/types.ts` | TypeScript DTOs mirroring backend models |
| `app/page.tsx` | Root dashboard |

### Shared Package

`packages/shared/src/types/` — TypeScript DTOs (`Project`, `Plan`, `Execution`, `ProjectRegistrationPayload`) used by both frontend and `lib/types.ts`.

## Tech Stack

- **Frontend:** Next.js 14, React 18, Tailwind CSS, TypeScript, Vitest
- **Backend:** FastAPI, SQLModel (SQLAlchemy), Pydantic v2, RQ + Redis, structlog
- **LLM:** Google Gemini (primary), OpenAI (alternate) — selected via `LLM_PROVIDER`
- **Vector DB:** Chroma (RAG/SOP matching)
- **Database:** SQLite (dev); Postgres-ready
- **Container:** Docker SDK (no raw shell commands)
- **Python:** 3.11+ required, 3.12 recommended

## Key Patterns

### Safety Gates (never bypass)
- `DRY_RUN=true` by default — execution is logged-only until disabled
- `ENABLE_LOCAL_EXECUTION=false` by default — must be true to run Docker commands
- `ALLOWED_REPO_ROOTS` — whitelist for allowed project paths
- All plans require explicit user approval before `Orchestrator` runs

### Code Conventions
- Python: `from __future__ import annotations`, `pathlib.Path` for paths, `structlog` with `.bind(component="...")`, explicit exception types
- Async FastAPI routes; CPU-bound work via `run_in_threadpool`
- Pydantic models use `Field(alias="...")` for API field name mapping
- TypeScript: `"use client"` only where interactivity is needed; API calls centralized in `lib/api.ts`
- Tailwind custom palette: `surface-900/800/700`, `accent-500/400/300`

### Rate Limits
- `POST /api/projects/register` and `POST /api/commands/parse`: 30 req/min per IP

## Environment Variables

Key vars in `.env` (see `.env.example`):

```
LLM_PROVIDER=GEMINI          # OLLAMA | OPENAI | GEMINI
GEMINI_API_KEY=...
OPENAI_API_KEY=...
DEPLOY_PROVIDER=local        # local | docker | vercel | render
DRY_RUN=true
ENABLE_LOCAL_EXECUTION=false
ALLOWED_REPO_ROOTS=          # empty = allow any (demo mode)
CORS_ORIGINS=http://localhost:3000
```

## Additional Context

- `devops_commander_context.md` — architectural memory doc (component overview, safety guarantees, known limitations)
- `docs/LOCAL-USER-GUIDE.md` — end-user setup guide
- `ROADMAP-NEXT-STEPS.md` — feature roadmap with ready-to-use Claude Code prompts
- Backend linting: Ruff configured in `pyproject.toml` (line-length 100, target py311)

<!-- code-review-graph MCP tools -->
## MCP Tools: code-review-graph

**IMPORTANT: This project has a knowledge graph. ALWAYS use the
code-review-graph MCP tools BEFORE using Grep/Glob/Read to explore
the codebase.** The graph is faster, cheaper (fewer tokens), and gives
you structural context (callers, dependents, test coverage) that file
scanning cannot.

### When to use graph tools FIRST

- **Exploring code**: `semantic_search_nodes` or `query_graph` instead of Grep
- **Understanding impact**: `get_impact_radius` instead of manually tracing imports
- **Code review**: `detect_changes` + `get_review_context` instead of reading entire files
- **Finding relationships**: `query_graph` with callers_of/callees_of/imports_of/tests_for
- **Architecture questions**: `get_architecture_overview` + `list_communities`

Fall back to Grep/Glob/Read **only** when the graph doesn't cover what you need.

### Key Tools

| Tool | Use when |
|------|----------|
| `detect_changes` | Reviewing code changes — gives risk-scored analysis |
| `get_review_context` | Need source snippets for review — token-efficient |
| `get_impact_radius` | Understanding blast radius of a change |
| `get_affected_flows` | Finding which execution paths are impacted |
| `query_graph` | Tracing callers, callees, imports, tests, dependencies |
| `semantic_search_nodes` | Finding functions/classes by name or keyword |
| `get_architecture_overview` | Understanding high-level codebase structure |
| `refactor_tool` | Planning renames, finding dead code |

### Workflow

1. The graph auto-updates on file changes (via hooks).
2. Use `detect_changes` for code review.
3. Use `get_affected_flows` to understand impact.
4. Use `query_graph` pattern="tests_for" to check coverage.
