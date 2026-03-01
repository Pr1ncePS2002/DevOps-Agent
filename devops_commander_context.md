# AI DevOps Commander — Context & Architectural Memory

> **Purpose**: Persistent architectural memory, refactor tracking, and source of truth for future AI agents and engineers.

---

## 1. Current System Capabilities

### 1.1 Supported Project Types

| Type | Detection | Dockerfile |
|------|-----------|------------|
| Node.js | `package.json` | Auto-generated if missing |
| Python | `requirements.txt` or `pyproject.toml` | Auto-generated if missing |
| Pre-containerized | Existing `Dockerfile` | Used as-is |

### 1.2 Deployment Flow

```
1. Register Project
   POST /projects/register { sourceType: "local"|"github", pathOrUrl }
   - Local: validate path exists, under ALLOWED_REPO_ROOTS (if set)
   - GitHub: clone into data/workspace

2. Upload .env
   POST /projects/{id}/env (multipart .env file)
   - Stored encrypted if ENCRYPTION_KEY set
   - Validates format; never logs secrets

3. Analyze (automatic on register)
   - Detect stack (node/python/docker)
   - Generate Dockerfile if missing
   - Return detected_stack, dockerfile_path

4. Parse Command → Plan Preview
   POST /commands/parse { project_id, text }
   - Structured DeploymentPlan with projectId, repoPath, detectedStack, dockerfilePath, imageTag, ports, envInjected
   - Enforces: no execution without .env, no execution without Dockerfile

5. Approve & Execute
   POST /executions/approve/{plan_id}
   - Orchestrator: validate → git pull (skipped) → docker build → docker run (--env-file) → health check → register deployment
   - Uses Docker Python SDK only (no raw shell)
   - Stores last-known-good tag on success

6. Watchdog (call evaluate_deployments periodically)
   - Checks container health
   - On failure: stop container, redeploy last-known-good
   - Rollback never fails silently

7. Manual Rollback
   POST /executions/{id}/rollback
   - Redeploys last-known-good image
```

### 1.3 Component Overview

| Layer | Technology |
|-------|------------|
| Frontend | Next.js + Tailwind, step-based wizard UI |
| Backend | FastAPI |
| Docker | Docker Python SDK (no raw shell) |
| Git | Whitelisted `git clone` only |
| Queue | Redis + RQ |
| DB | SQLModel + SQLite |
| Env storage | Encrypted (Fernet) if ENCRYPTION_KEY set |

---

## 2. Safety Guarantees

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

---

## 3. Known Limitations

- **DB schema**: New columns (Project.source_type, workspace_path, etc.) require fresh DB or manual migration. Delete `data/dev.db` to reset.
- **GitHub clone**: Uses `git clone --depth 1`; no `git pull` on subsequent deploys.
- **Watchdog**: Must be invoked externally (cron, RQ scheduler). No built-in periodic job.
- **ALLOWED_REPO_ROOTS**: Empty = allow any existing path (demo mode). Set for production.
- **Node.js default Dockerfile**: Assumes `npm start`; may need customization for non-standard projects.

---

## 4. Last Major Refactor Summary

**Date**: 2025-02-22

### Structural Changes

1. **Project Registration API**
   - `POST /projects/register` — local path or GitHub URL
   - `POST /projects/{id}/env` — .env upload
   - `GET /projects/{id}/analyze` — re-analyze stack

2. **Models**
   - Project: `source_type`, `workspace_path`, `detected_stack`, `dockerfile_path`, `has_env_file`, `last_known_good_tag`
   - Plan: `detected_stack`, `dockerfile_path`, `image_tag`, `ports_json`, `env_injected`
   - Deployment: new table for `container_id`, `image_tag`, `status`
   - Execution: `correlation_id`

3. **Orchestrator Refactor**
   - Removed raw `subprocess.run(npm)`
   - Uses Docker adapter: build_image, run_container, container_health_check, remove_container_safe
   - Steps: validate → build → run → health check → register
   - Stores last-known-good on success

4. **Docker Adapter** (`app/adapters/docker_adapter.py`)
   - `image_exists()`, `container_exists()`, `remove_container_safe()`
   - `build_image()` with log streaming
   - `run_container()` with env vars from file (no --env-file in SDK; reads file and passes as `environment`)

5. **Git Adapter** (`app/adapters/git_adapter.py`)
   - `clone_repo()` — whitelisted GitHub URLs only
   - No raw shell; uses `subprocess.run(["git", "clone", ...])`

6. **Env Storage** (`app/services/env_storage.py`)
   - Encrypted with Fernet if ENCRYPTION_KEY set
   - `get_env_for_docker()` returns decrypted path for container

7. **Watchdog** (`app/services/watchdog.py`)
   - `evaluate_deployments()` — check health, rollback on failure

8. **Frontend**
   - Step-based wizard: Add Project → Upload .env → Review Plan → Deploy → Logs & Status
   - Rollback button when last_known_good exists
   - `registerProject`, `uploadEnv`, `rollbackExecution` API calls

9. **Rollback**
   - `POST /executions/{id}/rollback` — manual rollback

---

## 5. Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| DEPLOY_PROVIDER | docker | docker \| vercel \| render |
| DRY_RUN | true | Log only, no execution |
| ENABLE_LOCAL_EXECUTION | false | Must be true for Docker deploy |
| ALLOWED_REPO_ROOTS | "" | Comma-separated paths for local projects |
| ENCRYPTION_KEY | (none) | Fernet key for .env encryption |

---

*Last updated: 2025-02-22*
