import asyncio
import logging
from contextlib import asynccontextmanager

from sqlalchemy import text

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.websocket import websocket_router
from app.api.v1.router import api_v1_router
from app.api.v1.schemas import ErrorDetail, error_response
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.db.runtime_schema import ensure_runtime_tables
from app.db.session import SessionLocal
from app.services import (
    EventPublisher,
    RealtimeMetrics,
    WebSocketConnectionManager,
    ensure_storage_tree,
)

logger = logging.getLogger(__name__)

async def overdue_checker_task():
    """Background task to automatically mark active contracts as overdue if due_date has passed."""
    while True:
        try:
            async with SessionLocal() as session:
                async with session.begin():
                    result = await session.execute(
                        text("""
                            UPDATE rental_contract
                            SET status = 'overdue', updated_at = CURRENT_TIMESTAMP
                            WHERE status = 'active'
                              AND due_date < CURRENT_TIMESTAMP
                              AND deleted_at IS NULL
                        """)
                    )
                    if result.rowcount > 0:
                        logger.info(f"Auto-marked {result.rowcount} contracts as overdue.")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Overdue checker failed: {e}")
        
        # Run every 1 hour
        await asyncio.sleep(3600)


def _extract_request_meta(request: Request) -> dict[str, str]:
    request_id = request.headers.get("x-request-id")
    if request_id:
        return {"request_id": request_id}
    return {}


def _http_detail_to_message(detail: object, fallback: str) -> str:
    if isinstance(detail, str):
        return detail
    return fallback


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    app.state.realtime_metrics = RealtimeMetrics()
    app.state.websocket_manager = WebSocketConnectionManager(
        max_connections=settings.ws_max_connections,
        message_size_limit_kb=settings.ws_message_size_limit_kb,
        metrics=app.state.realtime_metrics,
    )
    app.state.event_publisher = EventPublisher(
        app.state.websocket_manager,
        metrics=app.state.realtime_metrics,
    )
    await ensure_runtime_tables()
    
    # Khởi động background task
    overdue_task = asyncio.create_task(overdue_checker_task())
    
    try:
        yield
    finally:
        overdue_task.cancel()
        await app.state.websocket_manager.notify_shutdown()
        await app.state.event_publisher.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()
    logger.info("Configured CORS origins: %s", settings.cors_allow_origins)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):5173",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    storage_root = ensure_storage_tree().parent
    app.mount("/storage", StaticFiles(directory=str(storage_root)), name="storage")

    app.include_router(websocket_router)
    app.include_router(api_v1_router, prefix="/api/v1")

    @app.exception_handler(AppError)
    async def app_exception_handler(request: Request, exc: AppError) -> JSONResponse:
        details = None
        if exc.details:
            details = [ErrorDetail.model_validate(item) for item in exc.details]

        payload = error_response(
            code=exc.code,
            message=exc.message,
            details=details,
            meta=_extract_request_meta(request),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        payload = error_response(
            code=f"HTTP_{exc.status_code}",
            message=_http_detail_to_message(exc.detail, "Yeu cau khong hop le."),
            meta=_extract_request_meta(request),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details: list[ErrorDetail] = []
        for error in exc.errors():
            location = [str(part) for part in error.get("loc", []) if part != "body"]
            field_name = ".".join(location) if location else None
            details.append(
                ErrorDetail(
                    field=field_name,
                    message=error.get("msg", "Gia tri khong hop le."),
                    value=error.get("input"),
                )
            )

        payload = error_response(
            code="VALIDATION_ERROR",
            message="Du lieu dau vao khong hop le.",
            details=details,
            meta=_extract_request_meta(request),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=payload.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, _: Exception) -> JSONResponse:
        logger.exception("Unhandled exception while processing request")
        payload = error_response(
            code="INTERNAL_SERVER_ERROR",
            message="He thong tam thoi gian doan. Vui long thu lai.",
            meta=_extract_request_meta(request),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=payload.model_dump(),
        )

    return app


app = create_app()
