from __future__ import annotations

from app.common.settings import settings


def ensure_execution_allowed() -> None:
    if settings.dry_run:
        return
    if not settings.enable_local_execution:
        raise PermissionError(
            "Local execution is disabled. Set ENABLE_LOCAL_EXECUTION=true and DRY_RUN=false explicitly."
        )
