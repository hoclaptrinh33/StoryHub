from __future__ import annotations

from fastapi.testclient import TestClient

from tests.auth_helpers import build_auth_headers, ws_token


def _auth_headers(token: str) -> dict[str, str]:
    return build_auth_headers(token, include_branch=True)


def test_inventory_reservation_emits_complete_item_status_payload(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(f"/ws/item-live-updates?token={token}") as websocket:
        websocket.receive_json()

        response = client.post(
            "/api/v1/inventory/reservations",
            json={
                "item_id": "ITM-DORA01-001",
                "customer_id": 1,
                "reservation_minutes": 15,
                "request_id": "req-test-event-emission-reserve-001",
            },
            headers=_auth_headers("cashier-demo"),
        )
        assert response.status_code == 200

        event_payload = websocket.receive_json()

    assert event_payload["type"] == "item_status_changed"
    assert event_payload["event_id"]
    assert event_payload["item_id"] == "ITM-DORA01-001"
    assert event_payload["old_status"] == "available"
    assert event_payload["new_status"] == "reserved"
    assert event_payload["source_api"] == "inventory_reserve_item_v1"
    assert event_payload["changed_by"] == "cashier-01"
    assert event_payload["changed_at"]


def test_rental_return_emits_complete_settlement_payload(client: TestClient) -> None:
    token = ws_token("cashier-demo")
    with client.websocket_connect(f"/ws/item-live-updates?token={token}") as websocket:
        websocket.receive_json()

        response = client.post(
            "/api/v1/rentals/contracts/2001/return",
            json={
                "return_lines": [
                    {
                        "item_id": "ITM-CON98-001",
                        "condition_after": "good",
                    }
                ],
                "request_id": "req-test-event-emission-return-001",
            },
            headers=_auth_headers("cashier-demo"),
        )
        assert response.status_code == 200

        first = websocket.receive_json()
        second = websocket.receive_json()

    settlement = first if first["type"] == "rental_settlement_finished" else second

    assert settlement["type"] == "rental_settlement_finished"
    assert settlement["event_id"]
    assert settlement["settlement_id"]
    assert settlement["contract_id"] == "2001"
    assert isinstance(settlement["total_fee"], int)
    assert isinstance(settlement["refund_to_customer"], int)
    assert isinstance(settlement["remaining_debt"], int)
    assert settlement["settled_at"]
