"""
Shared test fixtures for the backend test suite.
Import this automatically via pytest's conftest mechanism.
"""
from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine


@pytest.fixture
def engine():
    """Create a fresh in-memory SQLite engine per test."""
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    """Provide a clean in-memory SQLite session per test."""
    with Session(engine, expire_on_commit=False) as s:
        yield s
