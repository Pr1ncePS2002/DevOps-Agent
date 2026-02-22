# Phase 2 Review — Anticipated Questions & Responses

These are focused on implementation details, integration risks, and how you prove safety with real executions.

| # | Panel Question | What You Say |
| --- | --- | --- |
| 1 | **“Is this really autonomous, or just a UI wrapper?”** | “The autonomy is in the agent graph: it converts intent into a step plan, checks SOPs via RAG, then orchestrates execution via adapters. The UI is intentionally only the interface and approval gate.” |
| 2 | **“How do you test the agent logic?”** | “We test at three layers: (1) command→plan parsing tests with fixed prompts, (2) policy/RAG validation tests with known SOP documents, and (3) orchestrator step-runner tests using mocked adapters to avoid real side effects.” |
| 3 | **“How do you ensure the worker can’t execute arbitrary code?”** | “Worker only calls adapter interfaces. Shell adapter only runs whitelisted scripts (repo-controlled), and Docker/Git adapters accept constrained inputs. The plan schema is validated server-side; anything out-of-schema is rejected.” |
| 4 | **“How do you prevent prompt injection from the command text?”** | “We don’t trust raw text. The LLM output must conform to a strict plan schema, then it goes through policy checks + RAG advisory, and finally requires explicit approval. No direct tool calls from prompts.” |
| 5 | **“What’s your rollback trigger?”** | “A combination of (a) execution step failures (non-zero exit codes) and (b) monitored signals like error-rate or latency p95 over a threshold for N intervals. Those thresholds are configured, and every rollback is logged as an incident event.” |
| 6 | **“What happens if the watchdog makes a wrong decision?”** | “The watchdog uses simple, explainable rules first (threshold breaches). We keep the rules deterministic and auditable. Any future ML/LLM classification remains advisory and still respects policy.” |
| 7 | **“How do you handle concurrency (two deployments at once)?”** | “Executions are isolated by plan/execution IDs. The queue handles parallel jobs with worker concurrency limits; the persistence layer tracks status transitions so UI can show per-execution logs without mixing.” |
| 8 | **“Why RQ instead of Celery/Kafka?”** | “RQ is lightweight and fits MVP scope. Our design isolates the queue boundary so we can swap to Celery or an event bus later if we need complex routing; Phase 2 validates workflow value before heavier infra.” |
| 9 | **“Can you prove this is safe?”** | “Safety is demonstrable: you can see plan approval, adapter restrictions, schema validation, and audit logs. We also run a negative demo: attempt unsafe request → system blocks or warns before execution.” |
| 10 | **“What is your definition of ‘done’ for Phase 2?”** | “At least one end-to-end deployment path executed through the real worker with real logs visible in UI, plus policy checks and at least one failure/rollback demonstration.” |
