from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Query, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.api.v1.dependencies import build_auth_context_from_token
from app.core.config import get_settings
from app.core.errors import AppError
from app.services import WebSocketConnectionLimitError, WebSocketConnectionManager

logger = logging.getLogger(__name__)

websocket_router = APIRouter(tags=["realtime"])


def _resolve_ws_token(token: str | None, authorization: str | None) -> str | None:
    if token:
        return token

    if not authorization:
        return None

    parts = authorization.split(" ", maxsplit=1)
    if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1].strip():
        return parts[1].strip()

    value = authorization.strip()
    return value or None


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _get_connection_manager(websocket: WebSocket) -> WebSocketConnectionManager:
    manager = getattr(websocket.app.state, "websocket_manager", None)
    if manager is None:
        raise RuntimeError("WebSocket manager is not initialized")
    return manager


@websocket_router.websocket("/ws/item-live-updates")
async def websocket_item_live_updates(
    websocket: WebSocket,
    token: str | None = Query(default=None),
    authorization: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    branch_id: str | None = Query(default=None),
) -> None:
    resolved_token = _resolve_ws_token(token, authorization)
    try:
        auth = build_auth_context_from_token(
            resolved_token,
            user_id=user_id,
            branch_id=branch_id,
        )
    except AppError:
        await websocket.close(code=4001, reason="AUTH_INVALID_TOKEN")
        return

    settings = get_settings()
    manager = _get_connection_manager(websocket)

    await websocket.accept()

    conn_id = uuid4().hex
    try:
        connection = await manager.connect(
            websocket,
            conn_id=conn_id,
            user_id=auth.user_id,
            role=auth.role,
            branch_id=auth.branch_id,
        )
    except WebSocketConnectionLimitError:
        await websocket.close(code=4429, reason="WS_CONNECTION_LIMIT")
        return

    await websocket.send_json(
        {
            "type": "connection_established",
            "connection_id": conn_id,
            "server_time": _now_iso(),
            "subscribed_events": sorted(connection.subscribed_events),
            "message_size_limit_kb": settings.ws_message_size_limit_kb,
        }
    )

    heartbeat_task = asyncio.create_task(
        _heartbeat_loop(
            manager=manager,
            conn_id=conn_id,
            interval_ms=settings.ws_heartbeat_interval_ms,
            max_missed_heartbeats=settings.ws_max_missed_heartbeats,
        )
    )

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await manager.send_json(
                    conn_id,
                    {
                        "type": "error",
                        "code": "WS_INVALID_MESSAGE",
                        "message": "Message must be valid JSON object.",
                    },
                )
                continue

            if not isinstance(message, dict):
                await manager.send_json(
                    conn_id,
                    {
                        "type": "error",
                        "code": "WS_INVALID_MESSAGE",
                        "message": "Message must be a JSON object.",
                    },
                )
                continue

            message_type = str(message.get("type", "")).lower()
            if message_type == "pong":
                await manager.mark_pong(conn_id)
                continue

            if message_type == "ping":
                await manager.send_pong(conn_id)
                continue

            if message_type == "subscribe":
                requested = [str(item) for item in message.get("events", []) if isinstance(item, str)]
                updated = await manager.add_subscriptions(conn_id, requested)
                await manager.send_json(
                    conn_id,
                    {
                        "type": "subscribed",
                        "events": sorted(updated),
                    },
                )
                continue

            if message_type == "unsubscribe":
                requested = [str(item) for item in message.get("events", []) if isinstance(item, str)]
                updated = await manager.remove_subscriptions(conn_id, requested)
                await manager.send_json(
                    conn_id,
                    {
                        "type": "unsubscribed",
                        "events": sorted(updated),
                    },
                )
                continue

            await manager.send_json(
                conn_id,
                {
                    "type": "error",
                    "code": "WS_UNSUPPORTED_MESSAGE",
                    "message": "Unsupported websocket message type.",
                },
            )
    except WebSocketDisconnect:
        logger.debug("Websocket disconnected: %s", conn_id)
    except Exception:
        logger.exception("Unexpected websocket error: %s", conn_id)
    finally:
        heartbeat_task.cancel()
        await asyncio.gather(heartbeat_task, return_exceptions=True)
        await manager.disconnect(conn_id)


async def _heartbeat_loop(
    *,
    manager: WebSocketConnectionManager,
    conn_id: str,
    interval_ms: int,
    max_missed_heartbeats: int,
) -> None:
    try:
        while True:
            await asyncio.sleep(interval_ms / 1000)

            missed_count = await manager.increment_missed_heartbeats(conn_id)
            if missed_count is None:
                return

            if missed_count > max_missed_heartbeats:
                await manager.disconnect(
                    conn_id,
                    close_code=4000,
                    reason="WS_HEARTBEAT_TIMEOUT",
                )
                return

            is_sent = await manager.send_ping(conn_id)
            if not is_sent:
                return
    except asyncio.CancelledError:
        return
