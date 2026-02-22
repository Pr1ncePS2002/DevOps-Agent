# Phase 3 Review Talk Track — Hardening, Security, and Scale

> Audience: review panel • Format: 12–15 minutes + reliability/security demo • Goal: show production-readiness direction: stronger guarantees, safer auth, cloud path, and measurable reliability.

## 1. Phase 3 Goal (0:00–1:00)
- Phase 1: design + DFD + rationale.
- Phase 2: working pipeline + real jobs.
- Phase 3: **make it dependable and scalable**: security controls, strong auditability, cloud-ready deployment, and measurable SLO/rollback performance.

## 2. What Phase 3 Adds (1:00–3:00)
- **Security**:
  - authentication/authorization for who can approve and execute
  - least-privilege adapter credentials
  - safer secret handling (environment + vault direction)
- **Reliability**:
  - idempotent steps; clearer retry semantics
  - watchdog tuning (debounce thresholds, confidence windows)
  - incident records and rollback traceability
- **Scalability**:
  - SQLite → Postgres
  - Chroma → PGVector (or managed vector store)
  - containerization and Kubernetes path
  - GitHub Actions deployment channel maturity

## 3. Demo Script (3:00–9:00)

### Demo A — Role-based Approval
- Show two users/roles conceptually:
  - Operator can propose plan
  - Approver can approve execution
- Demonstrate approval is blocked without correct role.

### Demo B — Reliability / Rollback Under Load
- Trigger a controlled error-rate spike (or simulate metrics values).
- Show watchdog logic:
  - metric crosses threshold for N intervals
  - rollback triggers
  - system records last-known-good redeploy
- Show audit trail: plan → approval → execution → incident → rollback result.

### Demo C — GitHub Actions Path
- Show a plan that chooses “GitHub Actions deploy” adapter:
  - workflow dispatch
  - run monitoring
  - status + logs summarized back into UI

## 4. Engineering Evidence (9:00–12:00)
- Present measurable artifacts:
  - migration proof: Postgres running, same plan/execution tables, improved concurrency
  - RAG store swap proof: embeddings searchable via PGVector (or a clearly documented migration)
  - security proof: least-privilege access patterns; secrets not stored in plain text
  - observability proof: Grafana dashboard screenshot + Prometheus metrics list

## 5. Why These Tools in Phase 3 (12:00–13:30)
- **Postgres**: correct concurrency + durable audit history.
- **PGVector**: vector search close to the data and scalable with DB ops.
- **Containerization/Kubernetes**: deployment parity with real org environments.
- **GitHub Actions**: standard CI/CD execution surface; integrates with existing org workflows.
- **Policy-first design**: reduces risk of “agent surprise” by constraining actions.

## 6. Closing (13:30–15:00)
- “Phase 3 shows not only that the agent works, but that it’s governable: secure approvals, measurable monitoring, deterministic rollback, and a clear path to cloud-scale operation.”
