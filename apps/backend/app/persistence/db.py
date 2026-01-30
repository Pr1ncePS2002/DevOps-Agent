from __future__ import annotations

from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.common.settings import get_database_url, settings


db_url = get_database_url()

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
    pool_pre_ping=True,
)


def init_db() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


@contextmanager
def session_scope() -> Session:
    with Session(engine) as session:
        yield session
