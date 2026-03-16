# Concerns

This document tracks technical debt, fragile areas, security concerns, performance bottlenecks, and unfinished architectural spikes.

## 🔴 Critical Issues

### 1. Weak Path Traversal Protection (Security)
**File:** `orchestrator.py:71`
```python
if ".." in workspace_path:
    raise ValueError("Invalid path: traversal not allowed")
```
- A simple substring check for `..` is easily bypassed (e.g. URL-encoded `%2e%2e` or using symlinks).
- **Fix:** Use `Path.resolve()` and validate it starts with an allowed base directory.

### 2. Bare `except` Blocks Silently Swallowing Errors
**Files:** `db.py:46`, `docker_adapter.py` (multiple locations), `orchestrator.py:150`
- The migration helper (`_migrate_project_table`) catches all exceptions and does nothing—if a real database error occurs (e.g. disk full, corrupted DB), it will be silently ignored.
- Docker adapter functions catch generic `Exception` everywhere, making debugging Docker connectivity issues very difficult.

### 3. Missing Foreign Key Constraints in SQLModel
**File:** `models.py`
- `Deployment.project_id`, `Plan.project_id`, `Execution.plan_id` are plain `int` fields, not `Field(foreign_key="project.id")`.
- This means orphaned records can exist after deleting a project—no cascade or referential integrity at the DB level.

---

## 🟡 Moderate Issues

### 4. Synchronous ORM Calls Inside FastAPI's Async Event Loop
**Files:** All route handlers in `routes/`
- FastAPI runs on an async event loop, but all database calls are synchronous SQLModel `Session` operations.
- Under concurrent load, this causes **thread starvation** because each request blocks the event loop during DB I/O.
- **Fix:** Either use `def` endpoints (which FastAPI auto-threads), mark heavy endpoints explicitly, or migrate to `AsyncSession`.

### 5. Docker Client Created Per-Call (Performance)
**File:** `docker_adapter.py:11-13`
- `_get_client()` creates a new `docker.from_env()` on every single call. During a build+run+health-check cycle, this means 5+ client instantiations.
- **Fix:** Use a module-level singleton or a context-managed pool.

### 6. No Status Transition Validation
**File:** `repositories.py` (`update_plan_status`, `set_execution_status`)
- Any status string can be set without validating allowed transitions (e.g. going from `succeeded` → `queued`).
- **Fix:** Add a state machine or at least a transition whitelist.

### 7. Session Scope Leak in Upload Endpoint
**File:** `routes/projects.py:62-90`
- The env upload endpoint opens TWO separate session scopes. Between the two sessions, the project could be deleted by another request, causing a silent no-op on the second `update_project`.

---

## 🟢 Minor / Improvement Opportunities

### 8. Excessive `getattr()` Usage in Project List Serialization
**File:** `routes/projects.py:150-161`
- Uses `getattr(p, "description", "")` on model fields that are always defined.
- This is defensive coding leftover from the migration—harmless but clutters the code.

### 9. No Frontend Testing Infrastructure
- `apps/frontend/package.json` has no test runner (Jest, Vitest, Playwright).
- All frontend behavior is untested.

### 10. Queue System Partially Removed
- `__pycache__` for `queue/tasks` and `queue/worker` were deleted in the last commit.
- The `executions.py` route still imports `from app.queue.queue import get_queue`, which will fail at runtime if the queue module is broken.

### 11. Import Inside Function Body (commands.py:53)
- `from app.services.command_interpreter import build_deployment_plan` is imported at line 53 inside the function, even though `interpret_command` is already imported from the same module at the top.
