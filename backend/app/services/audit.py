from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def write_audit_log(
    session: AsyncSession,
    *,
    actor_user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    ip_address: str | None,
    device_id: str | None,
) -> None:

    await session.execute(
        text(
            """
            INSERT INTO audit_log (
                actor_user_id,
                action,
                entity_type,
                entity_id,
                before_json,
                after_json,
                ip_address,
                device_id
            )
            VALUES (
                :actor_user_id,
                :action,
                :entity_type,
                :entity_id,
                :before_json,
                :after_json,
                :ip_address,
                :device_id
            );
            """
        ),
        {
            "actor_user_id": actor_user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "before_json": json.dumps(before, ensure_ascii=True) if before is not None else None,
            "after_json": json.dumps(after, ensure_ascii=True) if after is not None else None,
            "ip_address": ip_address,
            "device_id": device_id,
        },
    )
