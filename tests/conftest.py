"""Pytest fixtures. Isolate integration tests with in-memory SQLite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from football_engine.api.dependencies.session import get_db, get_session
from football_engine.infrastructure.db.models import Base
from football_engine.main import app


@pytest.fixture
def client() -> TestClient:
    """Test client with a fresh in-memory DB per test (StaticPool = single connection)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)

    def override_get_db():
        yield from get_session(factory)

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
