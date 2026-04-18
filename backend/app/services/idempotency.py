from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True, slots=True)
class CachedResponse:
    status_code: int
    payload: dict[str, Any]


async def get_cached_response(
    session: AsyncSession,
    *,
    scope: str,
    request_id: str,
) -> CachedResponse | None:
    result = await session.execute(
        text(
            """
            SELECT status_code, response_json
            FROM idempotency_record
            WHERE scope = :scope AND request_id = :request_id;
            """
        ),
        {"scope": scope, "request_id": request_id},
    )
    row = result.mappings().first()
    if row is None:
        return None

    return CachedResponse(
        status_code=int(row["status_code"]),
        payload=json.loads(row["response_json"]),
    )


async def store_cached_response(
    session: AsyncSession,
    *,
    scope: str,
    request_id: str,
    status_code: int,
    payload: dict[str, Any],
) -> CachedResponse:
    serialized_payload = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    await session.execute(
        text(
            """
            INSERT INTO idempotency_record (scope, request_id, status_code, response_json)
            VALUES (:scope, :request_id, :status_code, :response_json);
            """
        ),
        {
            "scope": scope,
            "request_id": request_id,
            "status_code": status_code,
            "response_json": serialized_payload,
        },
    )

    return CachedResponse(status_code=status_code, payload=payload)
