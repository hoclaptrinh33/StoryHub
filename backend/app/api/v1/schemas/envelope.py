from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    field: str | None = None
    message: str
    value: Any | None = None


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ResponseEnvelope[T](BaseModel):
    success: bool
    data: T | None = None
    error: ErrorPayload | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


def success_response[T](data: T, meta: dict[str, Any] | None = None) -> ResponseEnvelope[T]:
    return ResponseEnvelope(success=True, data=data, error=None, meta=meta or {})


def error_response(
    code: str,
    message: str,
    details: list[ErrorDetail] | None = None,
    meta: dict[str, Any] | None = None,
) -> ResponseEnvelope[None]:
    return ResponseEnvelope(
        success=False,
        data=None,
        error=ErrorPayload(code=code, message=message, details=details),
        meta=meta or {},
    )
