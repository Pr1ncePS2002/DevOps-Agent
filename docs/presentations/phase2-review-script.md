# Phase 2 Review Talk Track — Implementation & Integration

> Audience: review panel • Format: 12–15 minutes + live demo • Goal: prove the end-to-end pipeline works with real backend jobs (not mock data) and show safety controls in action.

## 1. What Changed Since Phase 1 (0:00–1:00)
- Phase 1 delivered architecture + DFD + rationale and UI/backend scaffolding.
- Phase 2 goal: **make the core loop real**: command → plan → approval → queue job → adapter steps → logs/metrics → watchdog decisions.

## 2. Phase 2 Deliverables (1:00–2:00)
- Working FastAPI endpoints for:
  - command parsing (creates plan)
  - plan retrieval (preview)
  - approval (enqueue execution)
  - execution status/log streaming
- RQ worker executing a controlled orchestration flow.
- At least one real adapter path (local mode) implemented end-to-end.
- UI showing real executions and live logs (not mock history).

## 3. Demo Script (2:00–8:00)
> Keep this demo tight: one happy path + one safety/rollback path.

### Demo A — Happy Path (deploy/test in dry-run or safe sandbox)
- Open the dashboard command console.
- Enter a command: “Deploy v1.6 to staging and run smoke tests”.
- Show plan preview:
  - structured steps (checkout → build → test → deploy)
  - environment target, version tag, risk notes
  - RAG/SOP advisory warnings (if any)
- Approve.
- Show execution:
  - execution job ID
  - step-by-step log stream
  - final status (succeeded)

### Demo B — Safety Gate / Failure Handling
- Submit a command that violates policy, e.g., “Run arbitrary shell script …”
- Show the system response:
  - plan preview contains warning/block reason
  - approval is prevented or requires explicit override justification (depending on your configured rule)
- Alternatively: force a failure in a controlled way (e.g., bad test command) and show:
  - watchdog flags failure
  - execution transitions to failed
  - (if enabled) rollback runs and final status becomes rolled_back

## 4. How the Pipeline Works (8:00–10:30)
- Walk the lifecycle in simple, repeatable terms (align to [AI-DevOps-Commander.md](../architecture/AI-DevOps-Commander.md)):
  1) UI sends natural language command
  2) API calls LangGraph CommandInterpreter → emits a Plan JSON
  3) RAGAdvisor checks SOP embeddings → attaches warnings/blocks
  4) Plan stored as `pending_approval`
  5) Approval enqueues RQ job
  6) Worker runs an ExecutionGraph calling adapters
  7) Watchdog evaluates logs + Prometheus metrics, triggers rollback if policy thresholds breach

## 5. Tools & Why (10:30–12:00)
- **FastAPI**: clear REST boundary and async-friendly request handling.
- **LangGraph**: makes the agent workflow explicit, testable, and auditable as a graph rather than “magic prompts”.
- **Redis + RQ**: separates request/response latency from long-running deploys; supports retries and worker scaling.
- **SQLite/Postgres**: audit trail of plans/executions; Postgres when concurrency and history grow.
- **Chroma (RAG)**: MVP vector store for SOP validation; will migrate to PGVector in Phase 3.
- **Prometheus/Grafana**: objective rollback signals (error rate, latency p95, crash loops).
- **Docker**: reproducible builds and controlled local deploy sandbox.

## 6. Evidence You Should Show (12:00–13:30)
- One slide: the DFD Level‑1, pointing to queue + adapters.
- One slide: execution timeline (plan created → approved → running → succeeded/failed).
- UI screenshots: plan preview screen + live log feed.
- A short snippet of stored plan JSON and execution record (fields: id, status transitions, timestamps).

## 7. What’s Next (13:30–15:00)
- Hardening steps: expand adapter coverage, add auth, add stronger policies, produce more monitoring dashboards.
- Scale steps: Postgres/PGVector + containerization + GitHub Actions adapter reliability.

## Closing Line
- “Phase 2 proves we can safely convert natural language into an auditable, approved, and executed DevOps workflow with real logs and clear rollback logic.”
