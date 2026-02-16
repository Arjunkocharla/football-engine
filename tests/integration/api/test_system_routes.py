from fastapi.testclient import TestClient

from football_engine.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"service": "football-engine", "status": "ok"}


def test_ready_endpoint_checks_db() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
