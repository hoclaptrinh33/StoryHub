from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.services.realtime_metrics import RealtimeMetrics

logger = logging.getLogger(__name__)

DEFAULT_SUBSCRIBED_EVENTS = frozenset(
    {
        "item_status_changed",
        "rental_settlement_finished",
    }
)


class WebSocketConnectionLimitError(Exception):
    """Raised when the websocket connection limit has been reached."""


@dataclass(slots=True)
class WebSocketConnection:
    conn_id: str
    websocket: WebSocket
    user_id: str
    role: str
    branch_id: str
    subscribed_events: set[str] = field(default_factory=lambda: set(DEFAULT_SUBSCRIBED_EVENTS))
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_pong_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    missed_heartbeats: int = 0


class WebSocketConnectionManager:
    def __init__(
        self,
        *,
        max_connections: int,
        message_size_limit_kb: int,
        allowed_events: set[str] | None = None,
        metrics: RealtimeMetrics | None = None,
    ) -> None:
        self.max_connections = max_connections
        self.message_size_limit_kb = message_size_limit_kb
        self.allowed_events = set(allowed_events or DEFAULT_SUBSCRIBED_EVENTS)
        self.metrics = metrics
        self._connections: dict[str, WebSocketConnection] = {}
        self._user_connections: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        *,
        conn_id: str,
        user_id: str,
        role: str,
        branch_id: str,
    ) -> WebSocketConnection:
        previous_connection: WebSocketConnection | None = None

        active_connections = 0
        async with self._lock:
            existing_conn_id = self._user_connections.get(user_id)
            if existing_conn_id is None and len(self._connections) >= self.max_connections:
                if self.metrics is not None:
                    await self.metrics.increment_connection_rejections()
                raise WebSocketConnectionLimitError

            if existing_conn_id:
                previous_connection = self._connections.pop(existing_conn_id, None)

            connection = WebSocketConnection(
                conn_id=conn_id,
                websocket=websocket,
                user_id=user_id,
                role=role,
                branch_id=branch_id,
                subscribed_events=set(DEFAULT_SUBSCRIBED_EVENTS),
            )
            self._connections[conn_id] = connection
            self._user_connections[user_id] = conn_id
            active_connections = len(self._connections)

        if self.metrics is not None:
            await self.metrics.set_active_connections(active_connections)

        if previous_connection is not None:
            await self._safe_close(
                previous_connection.websocket,
                code=4000,
                reason="WS_REPLACED_BY_NEW_CONNECTION",
            )

        return connection

    async def disconnect(
        self,
        conn_id: str,
        *,
        close_code: int | None = None,
        reason: str | None = None,
    ) -> None:
        connection: WebSocketConnection | None
        active_connections: int | None = None
        async with self._lock:
            connection = self._connections.pop(conn_id, None)
            if connection is None:
                return

            if self._user_connections.get(connection.user_id) == conn_id:
                self._user_connections.pop(connection.user_id, None)

            active_connections = len(self._connections)

        if self.metrics is not None and active_connections is not None:
            await self.metrics.set_active_connections(active_connections)

        if close_code is not None:
            await self._safe_close(connection.websocket, code=close_code, reason=reason)

    async def get_connection_count(self) -> int:
        async with self._lock:
            return len(self._connections)

    async def mark_pong(self, conn_id: str) -> None:
        async with self._lock:
            connection = self._connections.get(conn_id)
            if connection is None:
                return
            connection.last_pong_at = datetime.now(UTC)
            connection.missed_heartbeats = 0

    async def increment_missed_heartbeats(self, conn_id: str) -> int | None:
        async with self._lock:
            connection = self._connections.get(conn_id)
            if connection is None:
                return None
            connection.missed_heartbeats += 1
            return connection.missed_heartbeats

    async def add_subscriptions(self, conn_id: str, events: list[str]) -> set[str]:
        normalized = self._normalize_events(events)
        async with self._lock:
            connection = self._connections.get(conn_id)
            if connection is None:
                return set()
            connection.subscribed_events.update(normalized)
            return set(connection.subscribed_events)

    async def remove_subscriptions(self, conn_id: str, events: list[str]) -> set[str]:
        normalized = self._normalize_events(events)
        async with self._lock:
            connection = self._connections.get(conn_id)
            if connection is None:
                return set()
            connection.subscribed_events.difference_update(normalized)
            return set(connection.subscribed_events)

    async def send_ping(self, conn_id: str) -> bool:
        return await self.send_json(
            conn_id,
            {
                "type": "ping",
                "timestamp": self._utc_now_iso(),
            },
        )

    async def send_pong(self, conn_id: str) -> bool:
        return await self.send_json(
            conn_id,
            {
                "type": "pong",
                "timestamp": self._utc_now_iso(),
            },
        )

    async def send_json(self, conn_id: str, message: dict[str, Any]) -> bool:
        connection: WebSocketConnection | None
        async with self._lock:
            connection = self._connections.get(conn_id)

        if connection is None:
            return False

        payload = self._build_payload(message)
        if payload is None:
            return False

        try:
            await connection.websocket.send_json(payload)
            return True
        except Exception:
            logger.warning("Failed to send websocket message to %s", conn_id, exc_info=True)
            await self.disconnect(conn_id)
            return False

    async def broadcast(
        self,
        *,
        event_name: str,
        payload: dict[str, Any],
        branch_id: str | None,
        allowed_roles: set[str] | None = None,
    ) -> int:
        message = dict(payload)
        message["type"] = event_name

        safe_payload = self._build_payload(message)
        if safe_payload is None:
            return 0

        async with self._lock:
            recipients = [
                connection
                for connection in self._connections.values()
                if self._can_receive_event(
                    connection=connection,
                    event_name=event_name,
                    branch_id=branch_id,
                    allowed_roles=allowed_roles,
                )
            ]

        if not recipients:
            return 0

        sent_count = 0
        failed_connection_ids: list[str] = []
        for connection in recipients:
            try:
                await connection.websocket.send_json(safe_payload)
                sent_count += 1
            except Exception:
                logger.warning(
                    "Failed to broadcast event %s to websocket %s",
                    event_name,
                    connection.conn_id,
                    exc_info=True,
                )
                failed_connection_ids.append(connection.conn_id)

        for connection_id in failed_connection_ids:
            await self.disconnect(connection_id)

        if failed_connection_ids and self.metrics is not None:
            await self.metrics.record_broadcast_failure(len(failed_connection_ids))

        return sent_count

    async def notify_shutdown(self) -> None:
        async with self._lock:
            all_connections = list(self._connections.values())

        if not all_connections:
            return

        shutdown_message = {
            "type": "server_shutdown",
            "message": "Realtime service is restarting.",
            "timestamp": self._utc_now_iso(),
        }

        for connection in all_connections:
            try:
                await connection.websocket.send_json(shutdown_message)
            except Exception:
                logger.debug(
                    "Unable to send shutdown notice to websocket %s",
                    connection.conn_id,
                    exc_info=True,
                )

        await asyncio.sleep(2)

        for connection in all_connections:
            await self.disconnect(connection.conn_id, close_code=1001, reason="SERVER_SHUTDOWN")

    def _normalize_events(self, events: list[str]) -> set[str]:
        return {event for event in events if event in self.allowed_events}

    def _can_receive_event(
        self,
        *,
        connection: WebSocketConnection,
        event_name: str,
        branch_id: str | None,
        allowed_roles: set[str] | None,
    ) -> bool:
        if event_name not in connection.subscribed_events:
            return False

        if allowed_roles is not None and connection.role not in allowed_roles:
            return False

        if connection.role == "owner":
            return True

        if branch_id is None:
            return True

        return connection.branch_id == branch_id

    def _build_payload(self, message: dict[str, Any]) -> dict[str, Any] | None:
        payload_size = len(json.dumps(message, ensure_ascii=True).encode("utf-8"))
        if payload_size > self.message_size_limit_kb * 1024:
            logger.warning(
                "Dropped websocket message larger than configured limit (%s KB)",
                self.message_size_limit_kb,
            )
            return None
        return message

    @staticmethod
    async def _safe_close(websocket: WebSocket, *, code: int, reason: str | None) -> None:
        if websocket.client_state != WebSocketState.CONNECTED:
            return
        try:
            await websocket.close(code=code, reason=reason)
        except Exception:
            logger.debug("Websocket close failed", exc_info=True)

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
