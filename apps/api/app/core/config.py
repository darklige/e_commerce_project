from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Commerce Platform API"
    app_env: str = "local"
    app_version: str = "0.1.0"
    api_cors_origins: str = "http://localhost:3000"
    allowed_hosts: str = "localhost,127.0.0.1,0.0.0.0,testserver"
    jwt_secret_key: str = "change-this-local-development-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = Field(
        default="postgresql+psycopg://commerce:commerce@localhost:55432/commerce"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if "*" in self.cors_origins:
            raise ValueError("API_CORS_ORIGINS cannot include * while credentials are enabled")
        if (
            self.app_env == "production"
            and self.jwt_secret_key == "change-this-local-development-secret"
        ):
            raise ValueError("JWT_SECRET_KEY must be configured for production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
