# AI DevOps Commander – Architecture

Date: 2025-11-27

## Overview
AI DevOps Commander is an intelligent, autonomous DevOps agent that converts natural-language commands into safe, auditable deployment workflows. It runs locally first, with a path to scale to cloud environments.

- Frontend: Next.js + TailwindCSS + ShadCN UI
- Backend: FastAPI (Python)
- Agents: LangGraph (Python)
- LLM: Provider-based (Ollama / OpenAI / Gemini)
- Vector DB: Chroma (MVP), PGVector (later)
- Database: SQLite (MVP) → Postgres (scale)
- Queue: Redis + RQ
- Monitoring: Prometheus + Grafana
- Container: Docker Desktop / Rancher Desktop

## High-Level Components
- Next.js UI: Command input, plan preview, dashboards (logs, metrics, history)
- API Gateway (FastAPI): REST endpoints for parse/plan/execute/status/RAG
- Agents Layer (LangGraph):
  - CommandInterpreterAgent: parse NL → structured plan
  - RAGAdvisorAgent: validate plan against SOPs via vector search
  - ExecutionGraph: orchestrates build/test/deploy/monitor
  - WatchdogAgent: monitors error-rate/logs; triggers rollback
- Adapters (MCP-style, sandboxed): Git, Docker, Shell (whitelist), Monitoring (Prometheus), VectorStore (Chroma)
- Queue: RQ + Redis for long-running jobs and watchdog schedule
- Persistence: SQLite (plans, executions, history, embeddings metadata)
- Monitoring: Prometheus client in API; Grafana dashboards
- LLM: Provider clients (Ollama HTTP / OpenAI / Gemini)

## Safety Requirements
- Mandatory plan preview approval before execution
- Narrow, least-privilege adapters; no raw shell execution
- Rollback never fails silently; track last-known-good image tag
- Structured logging with correlation IDs per plan/job
- Thresholds configurable via ENV

## Data Flow (Command Lifecycle)
1) User submits text → /commands/parse
2) CommandInterpreterAgent → Plan JSON (pending_approval)
3) RAGAdvisorAgent cross-checks plan against SOP embeddings (warnings if deviation)
4) Plan stored; returned for preview
5) User approves → /plans/{id}/approve
6) ExecutionOrchestrator enqueues job → sequence graph:
   git checkout → docker build → docker run → tests → register monitor
7) WatchdogAgent evaluates metrics/logs; triggers rollback if thresholds exceeded
8) Rollback deploys last-known-good tag; incident logged

## ASCII Diagram

```
                +-------------------+
                |    Next.js UI     |
                | Cmd Input / Dash  |
                +---------+---------+
                          |
                          v
                    +-----------+          +------------------+
User Natural Cmd --> |  API     |<-------->|  Auth (future)   |
                     | Gateway  |          +------------------+
                          |
          +---------------+---------------------+
          |                                     |
          v                                     v
 +-------------------+                 +--------------------+
 | CommandInterpreter|                 |   RAGAdvisorAgent  |
 | (LangGraph Node)  |----Embeddings-->|  (VectorStore)     |
 +---------+---------+                 +---------+----------+
           | Parsed Plan (pending)               |
           +----------------------+              |
                                  v             |
                            +-----------+       |
                            |  Plan DB  |<------+
                            +-----+-----+
                                  |
                          Approval (UI)
                                  v
                          +--------------+
                          | Orchestrator |---Queue--> RQ/Redis
                          +--+-------+---+
                             |       |
                      Steps Graph   |
                       (Git/Docker) |
                             v       v
                      +------+       +------------------+
                      |Adapters|     | WatchdogAgent    |
                      |(Git,   |<----| metrics/log eval |
                      |Docker, |     +---------+--------+
                      |Shell,  |               |
                      |Monitor)|               v
                      +--+-----+        +--------------+
                         |              | Rollback Ops |
                         v              +------+-------+
                   +-----------+               |
                   | Prometheus|<--------------+
                   +-----------+
```

## Core Types (DTOs)
```ts
export interface DeploymentPlan {
  id: string;
  action: 'deploy' | 'rollback' | 'test' | 'build';
  version?: string;
  environments: string[];
  postSteps: string[]; // e.g., ['run_tests']
  warnings?: string[];
  status: 'pending_approval' | 'approved' | 'running' | 'failed' | 'rolled_back' | 'succeeded';
  createdAt: string;
  updatedAt: string;
}

export interface Orchestrator {
  execute(plan: DeploymentPlan): Promise<string>; // job id
  rollback(planId: string): Promise<void>;
}

export interface Watchdog {
  evaluateActiveDeployments(): Promise<void>;
}

export interface GitAdapter {
  checkout(ref: string): Promise<void>;
  latestCommit(): Promise<string>;
}

export interface DockerAdapter {
  build(tag: string, context: string): Promise<void>;
  run(tag: string, opts: { name?: string; ports?: string[]; env?: Record<string, string> }): Promise<string>; // returns container id
  stop(containerId: string): Promise<void>;
  logs(containerId: string): Promise<string>;
}

export interface MonitoringAdapter {
  getErrorRate(service: string): Promise<number>;
  getLatencyP95(service: string): Promise<number>;
}
```

## FastAPI Modular Layout (MVP)
- api/: routers (commands, plans, executions, status, rag)
- agents/: CommandInterpreterAgent (LangGraph), RAGAdvisorAgent, WatchdogAgent
- orchestrator/: execution graph + step runner
- adapters/: Docker, Git, Shell (whitelist), Monitoring (Prometheus), Vector (Chroma)
- queue/: RQ workers + schedulers
- persistence/: SQLModel/SQLAlchemy + repositories (SQLite → Postgres)
- common/logging/: structured logging + correlation IDs
- common/safety/: plan approvals, policy thresholds

## Scaling Path
- Split agents and orchestrator into microservices (FastAPI services)
- SQLite → Postgres (same ORM), Chroma → PGVector
- Containerize and orchestrate with Kubernetes
- Event bus (NATS/Kafka) for cross-service decoupling
- Horizontal scale RQ workers via concurrency and shards
- Multi-model support (Ollama local + remote fallbacks)

## Environment Variables (MVP)
See `.env.example` in repo root for local defaults.

## SOP/RAG
- Ingest playbooks (.md, .pdf → text), chunk and embed via Ollama embeddings
- Store in Chroma; attach plan warnings when deviation detected
- Block execution if deviation severity high (configurable)

## Security & Safety
- No direct shell; only whitelisted scripts from `infra/scripts`
- Narrow adapter interfaces, no raw process escapes
- Mandatory PLAN PREVIEW; write-once audit trail of decisions
- Rollback checks last-known-good image tag exists before deploy
