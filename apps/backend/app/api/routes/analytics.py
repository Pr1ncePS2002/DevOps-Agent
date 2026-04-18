from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.persistence.db import session_scope
from app.persistence.models import Deployment, Execution, Plan, Project

log = structlog.get_logger().bind(component="analytics")

router = APIRouter()


# ── Response models ───────────────────────────────────────────────────────────


class DayBucket(BaseModel):
    date: str
    count: int
    successes: int
    failures: int


class TopProject(BaseModel):
    name: str
    count: int


class RecentActivity(BaseModel):
    timestamp: str
    action: str
    project: str
    environment: str
    status: str
    duration_seconds: float | None


class AnalyticsSummary(BaseModel):
    total_deployments: int
    success_rate: float
    average_deploy_time_seconds: float
    rollback_count: int
    deployments_by_day: list[DayBucket]
    deployments_by_environment: dict[str, int]
    most_deployed_project: TopProject | None
    recent_activity: list[RecentActivity]


# ── Helpers ───────────────────────────────────────────────────────────────────


def _duration_seconds(exec_row: Execution) -> float | None:
    if exec_row.started_at and exec_row.finished_at:
        return (exec_row.finished_at - exec_row.started_at).total_seconds()
    return None


def _iso_date(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


# ── Route ─────────────────────────────────────────────────────────────────────


@router.get("/summary", response_model=AnalyticsSummary)
async def get_analytics_summary() -> AnalyticsSummary:
    """Return aggregated deployment analytics across all projects."""
    with session_scope() as s:
        # Load all executions joined with their plans
        rows = list(
            s.exec(
                select(Execution, Plan, Project)
                .join(Plan, Execution.plan_id == Plan.id)
                .join(Project, Plan.project_id == Project.id)
                .order_by(Execution.created_at.desc())
            ).all()
        )

        if not rows:
            return AnalyticsSummary(
                total_deployments=0,
                success_rate=0.0,
                average_deploy_time_seconds=0.0,
                rollback_count=0,
                deployments_by_day=[],
                deployments_by_environment={},
                most_deployed_project=None,
                recent_activity=[],
            )

        total = len(rows)
        successes = sum(1 for ex, _, _ in rows if ex.status == "succeeded")
        failures = sum(1 for ex, _, _ in rows if ex.status == "failed")
        rollbacks = sum(1 for ex, _, _ in rows if ex.status == "rolled_back")

        # Success rate
        terminal = successes + failures + rollbacks
        success_rate = round((successes / terminal) * 100, 1) if terminal else 0.0

        # Average deploy time (only finished executions)
        durations = [d for ex, _, _ in rows if (d := _duration_seconds(ex)) is not None]
        avg_time = round(sum(durations) / len(durations), 1) if durations else 0.0

        # Deployments by day
        import json

        day_counter: dict[str, dict[str, int]] = {}
        env_counter: Counter[str] = Counter()
        project_counter: Counter[str] = Counter()

        for ex, plan, project in rows:
            day = _iso_date(ex.created_at)
            bucket = day_counter.setdefault(day, {"count": 0, "successes": 0, "failures": 0})
            bucket["count"] += 1
            if ex.status == "succeeded":
                bucket["successes"] += 1
            elif ex.status in {"failed", "rolled_back"}:
                bucket["failures"] += 1

            # Environments
            try:
                envs = json.loads(plan.environments_json)
            except (json.JSONDecodeError, TypeError):
                envs = []
            for env in envs:
                env_counter[env] += 1

            project_counter[project.name] += 1

        by_day = sorted(
            [DayBucket(date=d, **v) for d, v in day_counter.items()],
            key=lambda b: b.date,
        )

        # Most deployed project
        top_project = None
        if project_counter:
            name, count = project_counter.most_common(1)[0]
            top_project = TopProject(name=name, count=count)

        # Recent activity (last 20)
        recent: list[RecentActivity] = []
        for ex, plan, project in rows[:20]:
            try:
                envs = json.loads(plan.environments_json)
            except (json.JSONDecodeError, TypeError):
                envs = []
            recent.append(
                RecentActivity(
                    timestamp=ex.created_at.isoformat() if isinstance(ex.created_at, datetime) else str(ex.created_at),
                    action=plan.action,
                    project=project.name,
                    environment=", ".join(envs) if envs else "default",
                    status=ex.status,
                    duration_seconds=_duration_seconds(ex),
                )
            )

        return AnalyticsSummary(
            total_deployments=total,
            success_rate=success_rate,
            average_deploy_time_seconds=avg_time,
            rollback_count=rollbacks,
            deployments_by_day=by_day,
            deployments_by_environment=dict(env_counter),
            most_deployed_project=top_project,
            recent_activity=recent,
        )
