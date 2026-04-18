from fastapi import APIRouter
from pydantic import BaseModel

from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.config import get_settings

router = APIRouter()


class HealthPayload(BaseModel):
    status: str
    service: str
    version: str
    environment: str


@router.get("/health", response_model=ResponseEnvelope[HealthPayload])
async def health_check() -> ResponseEnvelope[HealthPayload]:
    settings = get_settings()
    return success_response(
        HealthPayload(
            status="ok",
            service=settings.app_name,
            version=settings.app_version,
            environment=settings.environment,
        )
    )
