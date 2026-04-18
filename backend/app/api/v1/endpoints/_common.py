from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Request

from app.core.errors import AppError


def utc_now() -> datetime:
    return datetime.now(UTC).replace(microsecond=0)


def to_iso_z(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:  # pragma: no cover - guarded by validation in request models
        raise AppError(code="INVALID_DATETIME", message="Gia tri thoi gian khong hop le.") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def get_request_meta(request: Request) -> tuple[str | None, str | None]:
    ip_address = request.client.host if request.client else None
    device_id = request.headers.get("x-device-id")
    return ip_address, device_id
