from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from app.api.v1.dependencies import AuthContext, get_auth_context
from app.api.v1.schemas import ResponseEnvelope, success_response
from app.core.config import get_settings
from app.services.realtime_metrics import RealtimeMetrics

router = APIRouter()


class HealthPayload(BaseModel):
    status: str
    service: str
    version: str
    environment: str


class RealtimeLatencyMetricsPayload(BaseModel):
    count: int
    p50: float
    p95: float
    p99: float
    max: float


class RealtimeMetricsPayload(BaseModel):
    ws_connections_active: int
    ws_connection_rejections_total: int
    ws_events_published_total: dict[str, int]
    ws_event_latency_ms: RealtimeLatencyMetricsPayload
    ws_broadcast_failures_total: int
    generated_at: str


def _get_realtime_metrics(request: Request) -> RealtimeMetrics:
    realtime_metrics = getattr(request.app.state, "realtime_metrics", None)
    if realtime_metrics is None:
        raise RuntimeError("Realtime metrics service has not been initialized.")
    return realtime_metrics


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


@router.get(
    "/system/realtime/metrics",
    response_model=ResponseEnvelope[RealtimeMetricsPayload],
)
async def realtime_metrics_snapshot(
    request: Request,
    auth: AuthContext = Depends(get_auth_context),
) -> ResponseEnvelope[RealtimeMetricsPayload]:
    auth.require_role("manager", "owner")

    metrics = _get_realtime_metrics(request)
    snapshot = await metrics.snapshot()

    return success_response(RealtimeMetricsPayload.model_validate(snapshot))
