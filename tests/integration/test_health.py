from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_is_versioned() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert client.get("/health").status_code == 404
