"""Integration tests: create match, ingest events, get state and analytics."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from football_engine.main import app


@pytest.fixture
def client() -> TestClient:
    """Test client with a fresh in-memory DB per test (StaticPool = single connection)."""
    from football_engine.api.dependencies.session import get_db, get_session
    from football_engine.infrastructure.db.models import Base

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(
        bind=engine, autocommit=False, autoflush=False, expire_on_commit=False
    )

    def override_get_db():
        yield from get_session(factory)

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_create_match_and_get_state(client: TestClient) -> None:
    match_id = f"test-1-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/matches",
        json={"match_id": match_id, "home_team": "Team A", "away_team": "Team B"},
    )
    assert r.status_code == 201, r.json()
    body = r.json()
    assert body["match_id"] == match_id
    assert body["home_team"] == "Team A"
    assert body["score"]["home"] == 0
    assert body["status"] == "SCHEDULED"

    r2 = client.get(f"/api/v1/matches/{match_id}/state")
    assert r2.status_code == 200
    assert r2.json()["match_id"] == match_id


def test_ingest_event_and_analytics(client: TestClient) -> None:
    match_id = f"test-2-{uuid.uuid4().hex[:8]}"
    client.post(
        "/api/v1/matches",
        json={"match_id": match_id, "home_team": "X", "away_team": "Y"},
    )
    ev_id = f"ev-{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/events",
        json={
            "event_id": ev_id,
            "match_id": match_id,
            "clock": {"period": 1, "minute": 5, "second": 0},
            "team_side": "HOME",
            "event_type": "SHOT",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["accepted"] is True
    assert data["deduplicated"] is False
    assert data["match_state"]["match_id"] == match_id
    assert data["match_state"]["status"] == "LIVE"
    assert "analytics_latest" in data
    snap = data["analytics_latest"]
    assert "features_by_window" in snap
    assert "why" in snap
    assert "derived_metrics" in snap
    assert "deltas" in snap
    assert "pressure_index" in snap["derived_metrics"]
    assert "momentum" in snap["derived_metrics"]
    assert "field_tilt" in snap["derived_metrics"]
    assert "danger_next_5m" in snap["derived_metrics"]
    assert "HOME" in snap["derived_metrics"]["pressure_index"]
    assert "AWAY" in snap["derived_metrics"]["pressure_index"]
    assert "5m" in snap["features_by_window"] and "10m" in snap["features_by_window"]

    r2 = client.get(f"/api/v1/matches/{match_id}/analytics/latest")
    assert r2.status_code == 200
    assert r2.json()["match_id"] == match_id


def test_ingest_duplicate_event_is_idempotent(client: TestClient) -> None:
    match_id = f"test-3-{uuid.uuid4().hex[:8]}"
    client.post(
        "/api/v1/matches",
        json={"match_id": match_id, "home_team": "A", "away_team": "B"},
    )
    ev_id = f"ev-dup-{uuid.uuid4().hex[:8]}"
    payload = {
        "event_id": ev_id,
        "match_id": match_id,
        "clock": {"period": 1, "minute": 1, "second": 0},
        "team_side": "AWAY",
        "event_type": "CORNER",
    }
    r1 = client.post("/api/v1/events", json=payload)
    assert r1.status_code == 200
    assert r1.json()["deduplicated"] is False
    r2 = client.post("/api/v1/events", json=payload)
    assert r2.status_code == 200
    assert r2.json()["deduplicated"] is True
