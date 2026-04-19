from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from tests.auth_helpers import ws_token


def test_websocket_subscribe_and_unsubscribe_flow(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(
        f"/ws/item-live-updates?token={token}&user_id=ws-user-1"
    ) as websocket:
        handshake = websocket.receive_json()
        assert handshake["type"] == "connection_established"

        websocket.send_json({"type": "unsubscribe", "events": ["item_status_changed"]})
        unsubscribed = websocket.receive_json()
        assert unsubscribed["type"] == "unsubscribed"
        assert "item_status_changed" not in unsubscribed["events"]

        websocket.send_json({"type": "subscribe", "events": ["item_status_changed"]})
        subscribed = websocket.receive_json()
        assert subscribed["type"] == "subscribed"
        assert "item_status_changed" in subscribed["events"]


def test_websocket_ping_receives_pong(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(
        f"/ws/item-live-updates?token={token}&user_id=ws-user-2"
    ) as websocket:
        websocket.receive_json()
        websocket.send_json({"type": "ping", "timestamp": "2026-04-19T10:00:00Z"})
        pong = websocket.receive_json()

    assert pong["type"] == "pong"


def test_websocket_invalid_message_returns_error(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(
        f"/ws/item-live-updates?token={token}&user_id=ws-user-3"
    ) as websocket:
        websocket.receive_json()

        websocket.send_text("this is not json")
        error_payload = websocket.receive_json()
        assert error_payload["type"] == "error"
        assert error_payload["code"] == "WS_INVALID_MESSAGE"

        websocket.send_text("[]")
        error_payload = websocket.receive_json()
        assert error_payload["type"] == "error"
        assert error_payload["code"] == "WS_INVALID_MESSAGE"


def test_websocket_unsupported_message_returns_error(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(
        f"/ws/item-live-updates?token={token}&user_id=ws-user-4"
    ) as websocket:
        websocket.receive_json()

        websocket.send_json({"type": "unsupported_type"})
        payload = websocket.receive_json()

    assert payload["type"] == "error"
    assert payload["code"] == "WS_UNSUPPORTED_MESSAGE"


def test_websocket_duplicate_user_connection_replaces_old_connection(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(
        f"/ws/item-live-updates?token={token}&user_id=dup-user"
    ) as first_socket:
        first_socket.receive_json()

        with client.websocket_connect(
            f"/ws/item-live-updates?token={token}&user_id=dup-user"
        ) as second_socket:
            second_socket.receive_json()

            with pytest.raises(WebSocketDisconnect):
                first_socket.receive_json()
