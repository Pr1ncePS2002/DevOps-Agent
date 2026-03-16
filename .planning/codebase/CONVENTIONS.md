# Conventions

This document tracks coding style, module patterns, naming rules, and error handling.

## Code Style & Formatting
- **Backend (Python):** Follows PEP-8 conventions. Likely formatted via `black` or `ruff` given modern FastAPI standard practices.
- **Frontend (TypeScript/Next.js):** Follows standard ESLint configurations (`next lint`) and likely `prettier` for style.

## Architectural Patterns
- **API (FastAPI):**
  - Uses APIRouter components separated by domain (`providers.py`, `projects.py`, `executions.py`).
  - Strict type coercion via `Pydantic`.
- **Database Access:**
  - Repository Pattern used to decouple FastAPI routes from SQLModel execution. (e.g. `repositories.py`).
  - Separation of Concerns: routes handle HTTP input parsing, services handle complex logic/transformations, repositories handle data layer persistence.
- **Frontend Components:**
  - Next.js Client Components marked specifically for interactive areas.
  - Component segregation into business features (`project-registration`) vs layouts (`sections`).
  - Tailwind specific classes handled cleanly via utility strings or `clsx`/`tailwind-merge`.

## Naming Conventions
- **Python Backend:** `snake_case` for variables, functions, filenames. `PascalCase` for classes and Pydantic models.
- **TypeScript Frontend:** `kebab-case` for filenaming (`dashboard-client.tsx`), `PascalCase` for React components and Types (`DemoButton`, `ProjectRegistration`), `camelCase` for variables and hooks (`useProjectRegistration`).

## Error Handling
- **Backend API:** Uses FastAPI `HTTPException` where expected, returns standard JSON error bodies.
- **Frontend API Lib:** Utilizes `fetch` wrappers that check for `.ok` state.
