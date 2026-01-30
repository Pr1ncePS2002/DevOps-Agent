# Frontend (Next.js)

Next.js App Router + Tailwind UI for the AI DevOps Commander console. It talks to the FastAPI backend (default http://127.0.0.1:3001) to parse commands, approve plans, and stream execution logs.

## Stack

- Next.js 14 (App Router, React 18)
- Tailwind CSS with custom Space Grotesk / IBM Plex Sans pairing
- Lightweight primitives (no component kit) + lucide-react icons

## Local development

```bash
# from repo root
npm install
npm run dev --workspace apps/frontend
```

Environment knobs:

| Variable | Purpose | Default |
| --- | --- | --- |
| `NEXT_PUBLIC_API_BASE_URL` | Points UI to FastAPI server | `http://127.0.0.1:3001` |
| `NEXT_PUBLIC_POLL_INTERVAL_MS` | Execution log poll cadence | `2000` |
| `NEXT_PUBLIC_DRY_RUN` | Mirrors backend DRY_RUN to label stats | unset |

Backend must be running (see apps/backend/README.md). Redis + `run-worker` are required for approvals to stream logs.

## Project layout

```
app/
	layout.tsx      # Fonts + global chrome
	page.tsx        # Dashboard, command console, panels
components/
	command-console # Client component for parse/approve/log stream
	sections/       # Hero, stats, projects, history modules
lib/
	api.ts          # Thin fetch helpers for backend endpoints
	config.ts       # API base + polling interval
	types.ts        # Shared DTO types
```

## Next steps

1. Replace mocked execution history once backend exposes `/executions` listing.
2. Add auth (passport or headers) before exposing to staging.
3. Split dashboard/Projects/History into separate routes with URL state.