from __future__ import annotations

import asyncio

import pytest
from starlette.websockets import WebSocketState

from app.services.websocket_manager import (
    WebSocketConnectionLimitError,
    WebSocketConnectionManager,
)


class DummyWebSocket:
    def __init__(self) -> None:
        self.client_state = WebSocketState.CONNECTED
        self.sent_messages: list[dict[str, object]] = []
        self.closed_with: list[tuple[int, str | None]] = []

    async def send_json(self, payload: dict[str, object]) -> None:
        self.sent_messages.append(payload)

    async def close(self, code: int = 1000, reason: str | None = None) -> None:
        self.closed_with.append((code, reason))
        self.client_state = WebSocketState.DISCONNECTED


def _run[T](coroutine: asyncio.Future[T] | asyncio.Task[T] | asyncio.coroutines.Coroutine[object, object, T]) -> T:
    return asyncio.run(coroutine)


def test_connect_replaces_previous_user_connection() -> None:
    manager = WebSocketConnectionManager(max_connections=3, message_size_limit_kb=64)

    old_socket = DummyWebSocket()
    _run(
        manager.connect(
            old_socket,
            conn_id="conn-old",
            user_id="user-001",
            role="cashier",
            branch_id="main",
        )
    )

    new_socket = DummyWebSocket()
    _run(
        manager.connect(
            new_socket,
            conn_id="conn-new",
            user_id="user-001",
            role="cashier",
            branch_id="main",
        )
    )

    assert old_socket.closed_with == [(4000, "WS_REPLACED_BY_NEW_CONNECTION")]
    assert _run(manager.get_connection_count()) == 1


def test_connect_enforces_connection_limit() -> None:
    manager = WebSocketConnectionManager(max_connections=1, message_size_limit_kb=64)

    _run(
        manager.connect(
            DummyWebSocket(),
            conn_id="conn-1",
            user_id="user-001",
            role="cashier",
            branch_id="main",
        )
    )

    with pytest.raises(WebSocketConnectionLimitError):
        _run(
            manager.connect(
                DummyWebSocket(),
                conn_id="conn-2",
                user_id="user-002",
                role="cashier",
                branch_id="main",
            )
        )


def test_broadcast_filters_by_subscription_role_and_branch() -> None:
    manager = WebSocketConnectionManager(max_connections=8, message_size_limit_kb=64)

    cashier_main = DummyWebSocket()
    manager_branch_b = DummyWebSocket()
    owner_branch_b = DummyWebSocket()

    _run(
        manager.connect(
            cashier_main,
            conn_id="conn-cashier",
            user_id="cashier-1",
            role="cashier",
            branch_id="main",
        )
    )
    _run(
        manager.connect(
            manager_branch_b,
            conn_id="conn-manager",
            user_id="manager-1",
            role="manager",
            branch_id="branch-b",
        )
    )
    _run(
        manager.connect(
            owner_branch_b,
            conn_id="conn-owner",
            user_id="owner-1",
            role="owner",
            branch_id="branch-b",
        )
    )

    _run(manager.remove_subscriptions("conn-manager", ["item_status_changed"]))

    sent_count = _run(
        manager.broadcast(
            event_name="item_status_changed",
            payload={"event_id": "evt-001", "item_id": "ITM-001"},
            branch_id="main",
            allowed_roles={"cashier", "manager", "owner"},
        )
    )

    assert sent_count == 2
    assert len(cashier_main.sent_messages) == 1
    assert len(manager_branch_b.sent_messages) == 0
    assert len(owner_branch_b.sent_messages) == 1


def test_broadcast_drops_messages_over_size_limit() -> None:
    manager = WebSocketConnectionManager(max_connections=2, message_size_limit_kb=1)
    socket = DummyWebSocket()

    _run(
        manager.connect(
            socket,
            conn_id="conn-1",
            user_id="user-1",
            role="cashier",
            branch_id="main",
        )
    )

    sent_count = _run(
        manager.broadcast(
            event_name="item_status_changed",
            payload={"event_id": "evt-big", "body": "X" * 2048},
            branch_id="main",
            allowed_roles={"cashier"},
        )
    )

    assert sent_count == 0
    assert socket.sent_messages == []


def test_heartbeat_tracking_resets_after_pong() -> None:
    manager = WebSocketConnectionManager(max_connections=2, message_size_limit_kb=64)

    _run(
        manager.connect(
            DummyWebSocket(),
            conn_id="conn-1",
            user_id="user-1",
            role="cashier",
            branch_id="main",
        )
    )

    assert _run(manager.increment_missed_heartbeats("conn-1")) == 1
    assert _run(manager.increment_missed_heartbeats("conn-1")) == 2

    _run(manager.mark_pong("conn-1"))

    assert _run(manager.increment_missed_heartbeats("conn-1")) == 1
