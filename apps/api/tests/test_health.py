import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.main import create_app


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


def test_production_rejects_default_admin_invite_code() -> None:
    with pytest.raises(ValidationError, match="ADMIN_REGISTRATION_INVITE_CODE"):
        Settings(
            app_env="production",
            jwt_secret_key="production-test-secret-with-enough-entropy",
        )


def test_cors_rejects_wildcard_with_credentials() -> None:
    with pytest.raises(ValidationError, match="API_CORS_ORIGINS"):
        Settings(api_cors_origins="*")


def test_security_headers_are_set(client) -> None:
    response = client.get("/api/v1/health/live")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["permissions-policy"]


def test_untrusted_host_is_rejected(client) -> None:
    response = client.get("/api/v1/health/live", headers={"host": "evil.example"})

    assert response.status_code == 400


def test_production_hides_api_schema(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "production-test-secret-with-enough-entropy")
    monkeypatch.setenv("ADMIN_REGISTRATION_INVITE_CODE", "prod-admin-invite-code")
    get_settings.cache_clear()
    production_app = create_app()
    get_settings.cache_clear()

    with TestClient(production_app) as production_client:
        assert production_client.get("/openapi.json").status_code == 404
        assert production_client.get("/docs").status_code == 404
        assert production_client.get("/redoc").status_code == 404
