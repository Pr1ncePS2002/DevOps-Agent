# Architecture

This document tracks system design, data flow, abstractions, and core patterns.

## High-Level Architecture
This is a decoupled client-server architecture consisting of a Next.js frontend and a FastAPI backend responsible for orchestrating DevOps operations locally or in the cloud. The platform is named "AI DevOps Commander".

### Components
1. **Frontend (`apps/frontend`):**
   - Renders a React-based Dashboard.
   - Includes complex UI flows for creating and managing projects (`deployment-wizard.tsx`, `project-registration/*.tsx`).
   - Acts as an interface to send commands to the AI and read deployment/execution status.
2. **Backend API (`apps/backend/app/api`):**
   - FastAPI routers handling standard REST protocols (`commands.py`, `executions.py`, `projects.py`, `providers.py`).
   - Manages state, handles demo requests, and coordinates deployment checks.
3. **Services Layer (`apps/backend/app/services`):**
   - `command_interpreter`: Parses instructions from users/AI.
   - `deployers`: Abstract layer interfacing with Docker or Cloud SDKs.
   - `registration`: Unified project ingest (handles Git and environment matrix).
   - `orchestrator` & `watchdog`: Coordinates long-running tasks and monitors health.
4. **Persistence Layer (`apps/backend/app/persistence`):**
   - Uses Repository Pattern (`repositories.py`) for clean database abstraction.
   - Entity definition using SQLModel (`models.py`, `db.py`).
5. **Background Queue (`apps/backend/app/queue`):**
   - Uses `rq` and Redis to perform asynchronous operations without blocking the fast API routes.

## Data Flow
1. User interacts via the Next.js `dashboard-client` or `command-console`.
2. HTTP requests hit FastAPI `/api/routes/*`.
3. The API translates requests using the `services` layer.
4. If it's a sync request (e.g. read db), it calls the `repositories.py`.
5. If it's a long task (e.g. container deployment), it gets enqueued to RQ workers, which execute adapters (`docker_adapter.py`) behind the scenes and update the persistence layer when done.
