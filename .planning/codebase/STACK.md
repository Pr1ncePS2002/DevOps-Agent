# Tech Stack

This document tracks the technology stack, languages, frameworks, and core dependencies.

## Frontend
- **Framework:** Next.js 14.x (App Router implied by version)
- **Library:** React 18.x
- **Styling:** TailwindCSS 3.4.x, Autoprefixer, PostCSS
- **UI Components & Icons:** Lucide-React, `clsx`, `tailwind-merge`
- **Language:** TypeScript (v5.5.x)
- **Build Tool:** next CLI

## Backend
- **Framework:** FastAPI (v0.115)
- **Server:** Uvicorn
- **Language:** Python
- **Data Validation:** Pydantic (v2.10) & Pydantic Settings
- **ORM & Database:** SQLModel (v0.0.22), SQLAlchemy (v2.0) (Expected SQLite/PostgreSQL)
- **Background Jobs:** RQ (Redis Queue v2.1)
- **Caching/Queue Storage:** Redis
- **Containerization & Orchestration:** Docker CLI wrapper (`docker` pip package v7.1)
- **HTTP Client:** HTTPX
- **Logging:** Structlog
- **Security:** Cryptography (v43.0), python-multipart

## General Configuration
- **Package Managers:** npm (Frontend), pip (Backend)
- **Environment Variables:** `python-dotenv` and `.env` formats
- **Code Formatter/Linter:** ESLint (Frontend), expected Black/Ruff (Backend)
