from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.common.logging import logger
from app.common.settings import get_database_url, settings
from app.persistence import models  # noqa: F401 - register tables


db_url = get_database_url()

_connect_args: dict = {}
if db_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    _connect_args["timeout"] = 30  # wait up to 30s for a locked DB

engine = create_engine(
    db_url,
    connect_args=_connect_args,
    pool_pre_ping=True,
)


# Enable WAL mode for SQLite — allows concurrent reads while writing,
# which prevents "database is locked" errors when the orchestrator thread
# writes logs while the API thread polls for execution status.
if db_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()


def _migrate_project_table() -> None:
    """Add new columns to project table for existing DBs without dropping data."""
    if not db_url.startswith("sqlite"):
        return
    from sqlalchemy import text

    columns_to_add = [
        # Original columns
        ("source_type", "TEXT DEFAULT 'local'"),
        ("workspace_path", "TEXT"),
        ("detected_stack", "TEXT"),
        ("dockerfile_path", "TEXT"),
        ("has_env_file", "INTEGER DEFAULT 0"),
        ("last_known_good_tag", "TEXT"),
        # New columns added for unified registration (Phase 2)
        ("description", "TEXT NOT NULL DEFAULT ''"),
        ("branch", "TEXT"),
        ("deployment_platform", "TEXT NOT NULL DEFAULT 'docker'"),
        ("deployment_config_json", "TEXT NOT NULL DEFAULT '{}'"),
        ("env_config_json", "TEXT NOT NULL DEFAULT '{}'"),
    ]
    with engine.connect() as conn:
        for col, spec in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE project ADD COLUMN {col} {spec}"))
                conn.commit()
            except sqlite3.OperationalError:
                conn.rollback()
                # Column already exists — safe to ignore
            except Exception as exc:
                conn.rollback()
                logger.warning("migration_failed", column=col, error=str(exc))


def _migrate_plan_table() -> None:
    """Add new deployment columns to plan table for existing DBs."""
    if not db_url.startswith("sqlite"):
        return
    from sqlalchemy import text

    columns_to_add = [
        ("detected_stack", "TEXT"),
        ("dockerfile_path", "TEXT"),
        ("image_tag", "TEXT"),
        ("ports_json", "TEXT NOT NULL DEFAULT '[]'"),
        ("env_injected", "INTEGER NOT NULL DEFAULT 0"),
    ]
    with engine.connect() as conn:
        for col, spec in columns_to_add:
            try:
                conn.execute(text(f"ALTER TABLE plan ADD COLUMN {col} {spec}"))
                conn.commit()
            except sqlite3.OperationalError:
                conn.rollback()
            except Exception as exc:
                conn.rollback()
                logger.warning("migration_failed", column=col, error=str(exc))


def _migrate_chat_tables() -> None:
    """Create chat tables if they do not yet exist (safe for existing DBs)."""
    if not db_url.startswith("sqlite"):
        return
    from sqlalchemy import text

    create_session_sql = """
    CREATE TABLE IF NOT EXISTS chatsession (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT '',
        last_message_at TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'active'
    )
    """
    create_message_sql = """
    CREATE TABLE IF NOT EXISTS chatmessage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        message_type TEXT NOT NULL DEFAULT 'text',
        metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL DEFAULT ''
    )
    """
    with engine.connect() as conn:
        for stmt in (create_session_sql, create_message_sql):
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception as exc:
                conn.rollback()
                logger.warning("chat_migration_failed", error=str(exc))


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    _migrate_project_table()
    _migrate_plan_table()
    _migrate_chat_tables()
    # Deployment table is created fresh by create_all if it doesn't exist


@contextmanager
def session_scope() -> Session:
    with Session(engine, expire_on_commit=False) as session:
        yield session
