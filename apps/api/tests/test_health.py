from fastapi.testclient import TestClient

from app.main import app


def test_live_health() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_available() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Commerce Platform API"

