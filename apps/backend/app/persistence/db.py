from __future__ import annotations

from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.common.settings import get_database_url, settings
from app.persistence import models  # noqa: F401 - register tables


db_url = get_database_url()

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
    pool_pre_ping=True,
)


def _migrate_project_table() -> None:
    """Add new columns to project table for existing DBs."""
    if not db_url.startswith("sqlite"):
        return
    from sqlalchemy import text

    columns_to_add = [
        ("source_type", "TEXT DEFAULT 'local'"),
        ("workspace_path", "TEXT"),
        ("detected_stack", "TEXT"),
        ("dockerfile_path", "TEXT"),
        ("has_env_file", "INTEGER DEFAULT 0"),
        ("last_known_good_tag", "TEXT"),
    ]
    with engine.connect() as conn:
        for col, spec in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE project ADD COLUMN {col} {spec}"))
                conn.commit()
            except Exception:
                conn.rollback()
                # Column likely exists
                pass


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    _migrate_project_table()


@contextmanager
def session_scope() -> Session:
    with Session(engine) as session:
        yield session
