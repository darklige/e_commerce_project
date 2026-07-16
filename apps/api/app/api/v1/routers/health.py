from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings, get_settings
from app.db.health import check_database

SettingsDep = Annotated[Settings, Depends(get_settings)]

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
    version: str


class ReadinessResponse(HealthResponse):
    database: str


@router.get("/live")
def live(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        version=settings.app_version,
    )


@router.get("/ready")
def ready(settings: SettingsDep) -> ReadinessResponse:
    try:
        check_database()
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database is not ready",
        ) from exc

    return ReadinessResponse(
        status="ok",
        service=settings.app_name,
        environment=settings.app_env,
        version=settings.app_version,
        database="ok",
    )

