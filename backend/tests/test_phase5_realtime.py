from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from tests.auth_helpers import build_auth_headers, ws_token


def _auth_headers(token: str) -> dict[str, str]:
    return build_auth_headers(token, include_branch=True)


def test_realtime_websocket_handshake_success(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(f"/ws/item-live-updates?token={token}") as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "connection_established"
    assert payload["connection_id"]
    assert "item_status_changed" in payload["subscribed_events"]
    assert "rental_settlement_finished" in payload["subscribed_events"]


def test_realtime_websocket_rejects_invalid_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws/item-live-updates?token=invalid-token"):
            pass


def test_realtime_emits_item_status_for_inventory_reservation(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(f"/ws/item-live-updates?token={token}") as websocket:
        handshake = websocket.receive_json()
        assert handshake["type"] == "connection_established"

        response = client.post(
            "/api/v1/inventory/reservations",
            json={
                "item_id": "ITM-DORA01-001",
                "customer_id": 1,
                "reservation_minutes": 20,
                "request_id": "req-test-phase5-rt-reserve-001",
            },
            headers=_auth_headers("cashier-demo"),
        )
        assert response.status_code == 200

        event_payload = websocket.receive_json()
        assert event_payload["type"] == "item_status_changed"
        assert event_payload["item_id"] == "ITM-DORA01-001"
        assert event_payload["old_status"] == "available"
        assert event_payload["new_status"] == "reserved"


def test_realtime_emits_settlement_events_for_rental_return(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(f"/ws/item-live-updates?token={token}") as websocket:
        handshake = websocket.receive_json()
        assert handshake["type"] == "connection_established"

        response = client.post(
            "/api/v1/rentals/contracts/2001/return",
            json={
                "return_lines": [
                    {
                        "item_id": "ITM-CON98-001",
                        "condition_after": "good",
                    }
                ],
                "request_id": "req-test-phase5-rt-return-001",
            },
            headers=_auth_headers("cashier-demo"),
        )
        assert response.status_code == 200

        first_event = websocket.receive_json()
        second_event = websocket.receive_json()
        event_types = {first_event["type"], second_event["type"]}

        assert "item_status_changed" in event_types
        assert "rental_settlement_finished" in event_types

        settlement_event = (
            first_event
            if first_event["type"] == "rental_settlement_finished"
            else second_event
        )
        assert settlement_event["contract_id"] == "2001"
        assert settlement_event["settlement_id"]


def test_phase5_fallback_polling_endpoints(client: TestClient) -> None:
    inventory_status_response = client.get(
        "/api/v1/inventory/items/ITM-DORA01-001/status",
        headers=_auth_headers("cashier-demo"),
    )
    assert inventory_status_response.status_code == 200
    inventory_payload = inventory_status_response.json()
    assert inventory_payload["success"] is True
    assert inventory_payload["data"]["item_id"] == "ITM-DORA01-001"

    settlement_status_response = client.get(
        "/api/v1/rentals/contracts/2001/settlement",
        headers=_auth_headers("cashier-demo"),
    )
    assert settlement_status_response.status_code == 200
    settlement_payload = settlement_status_response.json()
    assert settlement_payload["success"] is True
    assert settlement_payload["data"]["contract_id"] == "2001"
