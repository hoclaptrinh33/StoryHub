from __future__ import annotations

from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

async def write_inventory_log(
    session: AsyncSession,
    *,
    user_id: str,
    action_type: str,
    target_type: str,
    target_id: str,
    title_name: str | None = None,
    sub_text: str | None = None,
    change_qty: int = 0,
    old_qty: int | None = None,
    new_qty: int | None = None,
    note: str | None = None,
) -> None:
    """
    Ghi log lịch sử cập nhật kho hàng.
    """
    await session.execute(
        text(
            """
            INSERT INTO inventory_log (
                user_id,
                action_type,
                target_type,
                target_id,
                title_name,
                sub_text,
                change_qty,
                old_qty,
                new_qty,
                note,
                created_at
            )
            VALUES (
                :user_id,
                :action_type,
                :target_type,
                :target_id,
                :title_name,
                :sub_text,
                :change_qty,
                :old_qty,
                :new_qty,
                :note,
                CURRENT_TIMESTAMP
            );
            """
        ),
        {
            "user_id": user_id,
            "action_type": action_type,
            "target_type": target_type,
            "target_id": target_id,
            "title_name": title_name,
            "sub_text": sub_text,
            "change_qty": change_qty,
            "old_qty": old_qty,
            "new_qty": new_qty,
            "note": note,
        },
    )
