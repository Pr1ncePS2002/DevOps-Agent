# AI DevOps Commander — Architecture

**Last updated**: 2026-03-15

## Overview

AI DevOps Commander converts natural-language commands into safe, auditable deployment workflows. It containerises apps via Docker Python SDK and triggers deployments on Vercel/Render via their APIs. Runs local-first with a path to cloud scale.

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14 + Tailwind CSS (port 3000) |
| Backend | FastAPI + Python (port 3001) |
| Docker | Docker Python SDK (no raw shell) |
| Git | Whitelisted `git clone` only |
| Queue | Redis + RQ |
| DB | SQLModel + SQLite |
| Env Storage | Fernet encryption (optional) |
| Cloud Deploy | Vercel API, Render API |

---

## Monorepo Layout

```
.
├─ apps/
│  ├─ backend/        # FastAPI API, orchestrator, adapters, deployers
│  │  ├─ app/
│  │  │  ├─ adapters/         # docker_adapter.py, git_adapter.py
│  │  │  ├─ api/routes/       # projects, commands, executions, providers, deploy_status, demo
│  │  │  ├─ common/           # settings.py, logging.py
│  │  │  ├─ persistence/      # models.py, repositories.py, db.py
│  │  │  ├─ queue/            # redis_conn, queue, tasks, worker
│  │  │  └─ services/
│  │  │     ├─ deployers/     # base, vercel, render, local
│  │  │     ├─ registration/  # service, schemas, env_matrix
│  │  │     ├─ orchestrator.py
│  │  │     ├─ watchdog.py
│  │  │     ├─ env_storage.py
│  │  │     ├─ project_analysis.py
│  │  │     └─ ...
│  │  └─ tests/
│  └─ frontend/       # Next.js UI
│     ├─ app/                 # page.tsx, layout.tsx
│     ├─ components/
│     │  ├─ project-registration/  # multi-step registration wizard
│     │  │  ├─ provider-connect.tsx # Vercel/Render OAuth connect
│     │  │  ├─ step-env.tsx         # guided .env builder
│     │  │  └─ ...
│     │  ├─ deployment-wizard.tsx   # main 5-step deploy flow
│     │  ├─ demo-button.tsx         # one-click demo mode
│     │  └─ sections/              # hero, stats, projects, history
│     └─ lib/                 # api.ts, types.ts, config.ts
├─ packages/
│  └─ shared/         # Shared TypeScript types (DTOs, ENV_MATRIX)
├─ infra/             # Placeholders for Docker, monitoring, scripts
└─ docs/
   └─ architecture/   # This document
```

---

## Data Models (SQLModel)

### Project
| Field | Type | Purpose |
|-------|------|---------|
| id | int (PK) | Auto-increment |
| name | str | Display name |
| description | str | User-provided |
| source_type | str | `local` / `github` |
| repo_path | str? | Local path |
| repo_url | str? | GitHub URL |
| branch | str? | Git branch |
| workspace_path | str? | Resolved path |
| detected_stack | str? | `node` / `python` / `docker` / `unknown` |
| dockerfile_path | str? | Path to Dockerfile |
| has_env_file | bool | Whether .env uploaded |
| last_known_good_tag | str? | For rollback |
| deployment_platform | str | `local` / `docker` / `vercel` / `render` |
| deployment_config_json | str | Platform-specific JSON |
| env_config_json | str | Registered env key names |

### Plan
| Field | Type | Purpose |
|-------|------|---------|
| id | int (PK) | |
| project_id | int (FK) | |
| raw_command | str | User NL text |
| action | str | `deploy` / `rollback` / `test` / `build` |
| environments_json | str | Target environments |
| detected_stack, dockerfile_path, image_tag, ports_json, env_injected | | Plan-level deploy config |
| status | str | `pending_approval` → `approved` → `running` → `succeeded`/`failed`/`rolled_back` |

### Execution
| Field | Type | Purpose |
|-------|------|---------|
| id | int (PK) | |
| plan_id | int (FK) | |
| status | str | `queued` → `running` → `succeeded`/`failed`/`rolled_back` |
| logs | str | Append-only execution log |
| correlation_id | str? | |

### Deployment
| Field | Type | Purpose |
|-------|------|---------|
| id | int (PK) | |
| project_id | int (FK) | |
| execution_id | int? | |
| container_id | str? | Docker container ID |
| image_tag | str? | |
| status | str | `pending` / `running` / `succeeded` / `failed` / `rolled_back` / `stopped` |

---

## API Routes

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/projects/register` | Unified project registration (source + platform + env) |
| POST | `/projects/{id}/env` | Upload .env file (encrypted at rest) |
| GET | `/projects/{id}/analyze` | Re-analyze project stack |
| GET | `/projects` | List all projects |
| POST | `/commands/parse` | NL → structured plan preview |
| POST | `/executions/approve/{plan_id}` | Approve plan → enqueue execution |
| POST | `/executions/{id}/rollback` | Manual rollback to last-known-good |
| GET | `/executions/{id}` | Get execution status + logs |
| POST | `/providers/vercel/connect` | Validate token, list Vercel projects |
| POST | `/providers/render/connect` | Validate API key, list Render services |
| POST | `/providers/encrypt-token` | Encrypt a provider token (Fernet) |
| GET | `/deploy/status/{provider}/{id}` | Poll cloud deploy status (normalised) |
| GET | `/demo/presets` | List demo project presets |
| POST | `/demo/setup/{index}` | One-click demo setup |
| GET | `/health` | Health check |

---

## Deployment Flow

```
1. Register Project
   POST /projects/register
   → Validate source × platform compatibility
   → Resolve/clone workspace
   → Detect stack (node/python/docker)
   → Auto-generate Dockerfile if missing
   → Persist project record

2. Upload .env
   POST /projects/{id}/env
   → Validate KEY=VALUE format
   → Encrypt with Fernet if ENCRYPTION_KEY set
   → Never log secrets

3. Parse Command → Plan Preview
   POST /commands/parse { project_id, text }
   → Structured DeploymentPlan with ports, image tag, stack info
   → RAG advisor warnings

4. Approve & Execute
   POST /executions/approve/{plan_id}
   → Enqueue via Redis + RQ
   → Orchestrator: validate → build → run → health check → register
   → Cloud: Vercel API / Render API deploy

5. Watchdog
   evaluate_deployments() (called periodically)
   → Check container health (with retries)
   → On failure: stop container, rollback to last-known-good

6. Manual Rollback
   POST /executions/{id}/rollback
   → Redeploy last-known-good image
```

---

## Docker Adapter

All Docker operations use the **Docker Python SDK** (no `subprocess` or shell commands).

- `build_image()` — streams build logs via callback, surfaces errors
- `run_container()` — reads .env file into `environment` list (SDK does NOT support `--env-file`)
- `container_health_check()` — retries with configurable interval
- `remove_container_safe()` — stop + remove, never NameError on client failure

---

## Cloud Deployers

### Vercel
- `_deploy_via_api()` — lists recent deployments, triggers redeploy
- `_deploy_via_git()` — for Git-connected projects
- `get_deployment_status()` — polls `/v13/deployments/{id}`

### Render
- `deploy()` — POST to `/v1/services/{id}/deploys`
- `get_deployment_status()` — GET deploy status
- `list_services()` — helper for provider connect

---

## Phase 3 UX Features

### 3a — Provider Connect
- Frontend `ProviderConnect` component for Vercel / Render
- Validates token → lists user's projects/services → auto-populates env vars
- Backend `/providers/vercel/connect` and `/providers/render/connect`
- Tokens encrypted via Fernet before storage

### 3b — Guided .env Builder
- `StepEnv` shows only fields relevant to the selected platform
- Field labels, placeholders, and help links (e.g. vercel.com/account/tokens)
- Client-side validation (port range, required fields)
- Sensitive fields use `type="password"`

### 3c — Deployment Status Polling
- Backend `/deploy/status/{provider}/{deployment_id}` normalises provider states
- Normalised states: `queued` → `building` → `deploying` → `live` / `failed`
- Frontend polls every 5s, shows live status badge + link to live URL on success

### 3d — One-Click Demo Mode
- Backend `/demo/presets` and `/demo/setup/{index}`
- Pre-configured Node.js and Python sample apps
- Pre-fills all config so user sees full flow without setup
- `DemoButton` component in hero banner and Add Project step

---

## Safety Guarantees

| Guarantee | Status |
|-----------|--------|
| Mandatory plan preview before execution | ✅ |
| Plan approval gate | ✅ |
| Dry-run default (configurable) | ✅ |
| ENABLE_LOCAL_EXECUTION gate | ✅ |
| No raw shell execution | ✅ (Docker SDK + whitelisted git clone) |
| Path traversal protection | ✅ |
| Last-known-good tag storage | ✅ |
| Watchdog auto-rollback | ✅ |
| .env stored encrypted (optional) | ✅ |
| Secrets never logged | ✅ |
| Provider tokens encrypted | ✅ |
| Health check with retries | ✅ |
| Decrypted temp files cleaned up | ✅ |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| DEPLOY_PROVIDER | docker | `docker` / `vercel` / `render` |
| DRY_RUN | true | Log only, no execution |
| ENABLE_LOCAL_EXECUTION | false | Must be true for Docker deploy |
| ALLOWED_REPO_ROOTS | "" | Comma-separated paths for local projects |
| ENCRYPTION_KEY | (none) | Fernet key for .env + token encryption |
| VERCEL_TOKEN | (none) | Vercel API token |
| VERCEL_ORG_ID | (none) | Vercel team/org ID |
| VERCEL_PROJECT_ID | (none) | Vercel project ID |
| RENDER_API_KEY | (none) | Render API key |
| RENDER_SERVICE_ID | (none) | Render service ID |

---

## Quick Start

1. Copy `.env.example` → `.env` and adjust values
2. **Backend**: `cd apps/backend && scripts\install.cmd && scripts\run-api.cmd` (port 3001)
3. **Redis**: `redis-server` (or `scripts\run-redis.cmd`)
4. **Worker**: `scripts\run-worker.cmd` (separate terminal)
5. **Frontend**: From root: `npm install && npm run dev --workspace apps/frontend` (port 3000)
