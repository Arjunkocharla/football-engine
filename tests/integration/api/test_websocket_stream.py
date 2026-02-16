"""Integration tests for WebSocket v2 streaming."""

import uuid

import pytest
from fastapi.testclient import TestClient


def test_websocket_subscription_and_broadcast(client: TestClient) -> None:
    """Test WebSocket subscription receives updates when events are ingested."""
    match_id = f"test-match-{uuid.uuid4().hex[:8]}"

    # Create match
    create_resp = client.post(
        "/api/v1/matches",
        json={
            "match_id": match_id,
            "home_team": "Team A",
            "away_team": "Team B",
        },
    )
    assert create_resp.status_code == 201

    # Connect WebSocket
    with client.websocket_connect(f"/ws/v2/matches/{match_id}/stream") as ws:
        # Receive connection confirmation
        welcome = ws.receive_json()
        assert welcome["type"] == "connected"
        assert welcome["match_id"] == match_id

        # Ingest an event
        event_id = f"event-{uuid.uuid4().hex[:8]}"
        ingest_resp = client.post(
            "/api/v1/events",
            json={
                "event_id": event_id,
                "match_id": match_id,
                "provider_name": "test",
                "provider_event_id": "p1",
                "clock": {"period": 1, "minute": 5, "second": 30},
                "team_side": "HOME",
                "event_type": "SHOT",
                "payload": {},
            },
        )
        assert ingest_resp.status_code == 200

        # Receive update via WebSocket
        update = ws.receive_json()
        assert update["type"] == "update"
        assert update["event"]["event_id"] == event_id
        assert update["event"]["event_type"] == "SHOT"
        assert update["match_state"]["match_id"] == match_id
        assert update["analytics_latest"] is not None
        assert "pressure_index" in update["analytics_latest"]["derived_metrics"]


def test_websocket_connection_limit(client: TestClient) -> None:
    """Test that connection limits are enforced (simplified - just verify first connection works)."""
    match_id = f"test-match-{uuid.uuid4().hex[:8]}"

    # Create match
    client.post(
        "/api/v1/matches",
        json={
            "match_id": match_id,
            "home_team": "Team A",
            "away_team": "Team B",
        },
    )

    # Connect WebSocket (should succeed)
    with client.websocket_connect(f"/ws/v2/matches/{match_id}/stream") as ws:
        welcome = ws.receive_json()
        assert welcome["type"] == "connected"
        assert welcome["match_id"] == match_id
