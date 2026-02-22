# Phase 3 Review — Anticipated Questions & Responses

These focus on security, production readiness, and scaling trade-offs.

| # | Panel Question | What You Say |
| --- | --- | --- |
| 1 | **“How do you secure approvals and prevent misuse?”** | “Approvals are authenticated and authorization-scoped. Only approved roles can execute; all actions are audited with timestamps and correlation IDs. Adapter credentials are least-privilege.” |
| 2 | **“Where do secrets live?”** | “In MVP, secrets come from environment variables and are never written to logs. For production, the plan is to integrate a secret store (e.g., Vault/Key Vault) and provide adapters with short-lived tokens.” |
| 3 | **“What if the agent becomes inconsistent at scale?”** | “We minimize LLM decision surface by enforcing a plan schema, deterministic policies, and approvals. At scale we rely more on rules + metrics; LLM remains a planner/advisor rather than an executor.” |
| 4 | **“How do you handle partial failures (some steps succeed, others fail)?”** | “ExecutionGraph records step-level status; rollback is a first-class action. Steps are made idempotent where possible; failures generate incidents with a deterministic remediation path.” |
| 5 | **“Why PGVector instead of a managed vector DB?”** | “PGVector keeps ops simple and co-locates vector search with transactional data. If scale demands, we can migrate to a managed vector service; the app uses a vector-store adapter boundary.” |
| 6 | **“Is GitHub Actions monitoring reliable enough for rollbacks?”** | “We monitor both workflow run status and service runtime metrics. A workflow success is not sufficient; the watchdog uses Prometheus signals to decide rollback.” |
| 7 | **“What’s your SLO/SLI story?”** | “SLIs include error-rate, latency p95, deployment success rate, and rollback time. SLO targets are defined per environment and enforced via watchdog thresholds.” |
| 8 | **“What prevents noisy rollbacks?”** | “Debounce windows (N consecutive intervals), minimum observation time, and multi-signal checks. Rollbacks are not triggered by a single blip.” |
| 9 | **“How do you ensure auditability?”** | “Every plan and execution has state transitions stored in Postgres, plus structured logs with correlation IDs. We can reconstruct who approved what, what ran, and what metric triggered rollback.” |
| 10 | **“What’s the biggest remaining risk?”** | “Over-reliance on LLM reasoning. The mitigation is keeping execution deterministic and policy-driven, with humans approving plans and metrics triggering rollbacks.” |
