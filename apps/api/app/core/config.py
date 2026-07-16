from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Commerce Platform API"
    app_env: str = "local"
    app_version: str = "0.1.0"
    api_cors_origins: str = "http://localhost:3000"
    database_url: str = Field(
        default="postgresql+psycopg://commerce:commerce@localhost:5432/commerce"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

