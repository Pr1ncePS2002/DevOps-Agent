# Directory Structure

This document outlines the repository layout and conventions.

## Root Level
- `apps/` - Monorepo-style application packages.
  - `backend/` - FastAPI python package.
  - `frontend/` - Next.js React package.
- `packages/` - Shared libraries (TypeScript).
- `docs/` - System architecture and product design documentation.
- `infra/` - Infrastructure as Code, deployment scripts, or docker-compose files.
- `.gemini/` - Contains the autonomous GSD multi-agent engineering framework.

## Backend Structure (`apps/backend/`)
- `app/`
  - `adapters/` - External interfaces (e.g. Docker Engine).
  - `api/`
    - `router.py` - Main FastAPI APIRouter configuration.
    - `routes/` - Endpoint handlers (commands, projects, executions).
  - `persistence/` - Data storage logic (SQLModel tables, Repositories layer).
  - `queue/` - Background workers and Redis logic.
  - `services/` - Business logic boundaries (orchestrator, command interpreter, unified project registration).
- `tests/` - Pytest suites.
- `requirements.txt` / `pyproject.toml` - Python dependency management.

## Frontend Structure (`apps/frontend/`)
- `app/` - Next.js App Router root pages and layouts.
- `components/` - Reusable React components.
  - `project-registration/` - Complex wizard steps to ingest source, env, and metadata.
  - `sections/` - Main page segments (`hero-banner`, `projects-panel`).
- `lib/` - Utilities and types (`api.ts`, `types.ts`).
- `tailwind.config.ts`, `postcss.config.mjs` - CSS configuration.

## Shared Structure (`packages/`)
- `shared/src/types/project.ts` - Shared typescript interfaces between node processes and potentially used as data definitions.
