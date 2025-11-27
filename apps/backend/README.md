# Backend (NestJS) – Placeholder

This directory will contain the NestJS API implementing:
- REST endpoints for command parse, plan preview, approval, execution, status
- Agents (LangGraph) for interpretation, RAG advisory, watchdog
- Orchestrator executing Git/Docker/Test/Monitor steps via adapters
- BullMQ workers and scheduled jobs
- Persistence (SQLite→Postgres)
- Structured logging and safety policies

Next step: scaffold via Nest CLI or manual modules as per architecture.