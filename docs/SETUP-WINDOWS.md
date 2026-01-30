# Windows Setup (Local-First)

These steps help you start without installing Ollama by using OpenAI or Gemini API keys. You can switch to Ollama later for 100% offline.

## 1) Prerequisites

Install Node.js LTS and Git (if `winget` is available):

```bat
winget install OpenJS.NodeJS.LTS
winget install Git.Git
```

If `winget` is not available on your machine, install manually:
- Node.js LTS: https://nodejs.org/
- Git: https://git-scm.com/downloads
- Python 3.12 (recommended) or 3.11: https://www.python.org/downloads/

Important: Python 3.14 is currently too new for some critical wheels (e.g., `pydantic-core`) on Windows. If you see pip errors mentioning `pydantic-core` and Rust/Cargo, install Python 3.12 and retry.

Optional (recommended): Docker Desktop to run Redis and other services locally:

```bat
winget install Docker.DockerDesktop
```

If you can't use Docker on Windows, consider Memurai (Redis-compatible) Community Edition: https://www.memurai.com/get-memurai

## 2) Clone and install dependencies

```bat
cd "c:\Users\psing\Desktop\DevOps Agent"
npm install
```

Backend (FastAPI) dependencies are installed via:
```bat
cd apps\backend
scripts\install.cmd
```

## 3) Configure environment

Copy the template and set your chosen LLM provider:

```bat
copy .env.example .env
```

Edit `.env` and set one of:

- Use OpenAI (no local installs needed):
  - `LLM_PROVIDER=OPENAI`
  - `OPENAI_API_KEY=sk-...`
  - Optional: `OPENAI_BASE_URL` if you use a compatible proxy
  - `OPENAI_MODEL=gpt-4o-mini` (or your preferred)

- Use Gemini (no local installs needed):
  - `LLM_PROVIDER=GEMINI`
  - `GEMINI_API_KEY=...`
  - `GEMINI_MODEL=gemini-1.5-pro`

- Use Ollama (local, offline):
  - Install Ollama: https://ollama.com/download
  - `LLM_PROVIDER=OLLAMA`
  - `OLLAMA_BASE_URL=http://localhost:11434`
  - `OLLAMA_MODEL=llama3.1:8b`

## 4) Redis (for queue)

For RQ jobs, run Redis. Easiest via Docker:

```bat
docker run --name redis -p 6379:6379 -d redis:7
```

Without Docker, install Memurai and set `REDIS_URL=redis://localhost:6379`.

## 5) Next steps

- Backend scaffold will add FastAPI services using the selected LLM provider (OPENAI/GEMINI/OLLAMA) behind a single interface.
- Frontend scaffold will allow: enter command → preview plan → approve → execute.
- You can proceed with keys now; no need to install Ollama if using OpenAI or Gemini.
