# Integrations

This document tracks external systems, APIs, and infrastructure integrations.

## Core Infrastructure
- **Docker Engine / Daemon:** The backend actively uses the `docker` python SDK to interface with local or remote Docker engines for project orchestration.
- **Redis:** Used heavily as the message broker for the RQ (Redis Queue) background task workers.
- **Relational Database:** Integrated via SQLModel/SQLAlchemy. Usually mapped to a local SQLite database or remote PostgreSQL instance in production.

## Service Providers (Project Registration)
The system has a module for unified project registration, hinting at connecting to multiple Git and Cloud Providers such as:
- **GitHub / GitLab:** Likely for source code pulling and webhooks.
- **Cloud Providers (AWS, GCP, Azure, Vercel):** Anticipated based on the `deployers` and `registration` contexts within the backend services.

## APIs and Clients
- **HTTP/REST:** Internal service communication, likely webhook posting and status checking using the `httpx` module.
