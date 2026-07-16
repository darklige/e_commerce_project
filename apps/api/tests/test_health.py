import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_live_health(client) -> None:
    response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_available(client) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Commerce Platform API"


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(app_env="production")


def test_cors_rejects_wildcard_with_credentials() -> None:
    with pytest.raises(ValidationError, match="API_CORS_ORIGINS"):
        Settings(api_cors_origins="*")
