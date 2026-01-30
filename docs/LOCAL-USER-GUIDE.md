# AI DevOps Commander — Local User Guide (Clone & Run)

This is the intended **local-first** usage flow: users clone the repo, install dependencies, add API keys, run the system locally, then point it at their project either via a **local repo path** or a **GitHub repo link**.

## 0) What the user installs first (one-time)

- Node.js LTS (for the web dashboard)
- Python 3.12 (recommended) or 3.11 (for FastAPI backend + agents)
- Git
- Optional: Docker Desktop (to run Redis locally, and to run Docker-based deployments)

## 1) Clone the AI DevOps Commander repo

```bat
cd %USERPROFILE%\Desktop
git clone <YOUR_AI_DEVOPS_COMMANDER_REPO_URL>
cd "AI DevOps Commander"
```

## 2) Configure environment variables (API keys)

Copy the template:

```bat
copy .env.example .env
```

Open `.env` and set:

- Pick one LLM provider:
  - `LLM_PROVIDER=OPENAI` (recommended if you don’t want Ollama installed)
  - OR `LLM_PROVIDER=GEMINI`
  - OR `LLM_PROVIDER=OLLAMA` (offline/local)

- Add your key:
  - If OpenAI: set `OPENAI_API_KEY=...`
  - If Gemini: set `GEMINI_API_KEY=...`

Keep the rest as defaults for local MVP.

## 3) Start Redis (required for background jobs)

Option A (recommended): Docker

```bat
docker run --name redis -p 6379:6379 -d redis:7
```

Option B: install a local Redis-compatible server (e.g., Memurai) and keep:
- `REDIS_URL=redis://localhost:6379`

## 4) Install dependencies

### Frontend (Next.js)

From repo root:

```bat
npm install
```

### Backend (FastAPI)

Use the provided backend scripts:

```bat
cd apps\backend
scripts\install.cmd
```

If you see: "'python' is not recognized", Python is not installed or not on PATH.
- Install Python 3.11+ from https://www.python.org/downloads/
- During install, enable: "Add python.exe to PATH"
- Close and re-open your terminal, then retry `scripts\install.cmd`

If dependency installation fails on Python 3.14 (often due to `pydantic-core` requiring Rust/Cargo), install Python 3.12 and rerun `scripts\install.cmd`.

## 5) Run the system locally

You run **3 processes** locally:
1) FastAPI API server
2) RQ worker (background job runner)
3) Next.js frontend

Example commands:

```bat
REM Terminal 1: Backend API
cd apps\backend
scripts\run-api.cmd
```

```bat
REM Terminal 2: RQ Worker
cd apps\backend
scripts\run-worker.cmd
```

```bat
REM Terminal 3: Frontend
cd apps\frontend
npm run dev
```

Then open the UI in your browser:
- `http://localhost:3000`

## 6) Add your project (the repo you want to deploy)

In the UI, click **Add Project**. You can onboard in two ways:

### Option A — Local repo path (already cloned)
- User provides a folder path, for example:
  - `C:\projects\my-service`
- The system checks:
  - it is a Git repo (has `.git/`)
  - deployment files exist (Dockerfile / compose / approved scripts)
- The system stores that path as the project’s working directory.

### Option B — GitHub repo link (agent clones locally)
- User provides a Git URL, for example:
  - `https://github.com/org/repo.git`
  - or `git@github.com:org/repo.git`
- The system clones the repo into a managed local folder (configured by env, not hard-coded), then stores the cloned path.

## 7) Run a deployment using human language

In the UI, type a command like:
- “Deploy v1.6 to staging and run tests”

The system will:
1) Parse your text into a structured plan
2) Check SOP/playbooks (RAG) and show warnings if the plan deviates
3) Show a **Plan Preview** (mandatory)
4) Only when you click **Approve**, it runs the plan

## 8) What happens during execution (local mode)

Typical safe workflow:
- `git checkout` target version
- `docker build`
- `docker run`
- run approved test script (whitelisted)
- monitor health (logs/metrics)
- rollback to last-known-good if watchdog triggers

## 9) What users do for their own projects (summary)

For each new project, they only need to:
- add the project (path or GitHub link)
- choose deployment style (local Docker vs GitHub Actions)
- add approved scripts (tests) into `infra/scripts` or project-specific allowlist
- (optional) upload SOPs/playbooks for RAG validation

That’s it — then they can deploy using human language through the dashboard.
