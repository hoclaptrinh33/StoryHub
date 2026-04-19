from __future__ import annotations

from fastapi.testclient import TestClient

from tests.auth_helpers import build_auth_headers


def _auth_headers(token: str) -> dict[str, str]:
    return build_auth_headers(token)


def test_inventory_reservation_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/inventory/reservations",
        json={
            "item_id": "ITM-DORA01-001",
            "customer_id": 1,
            "reservation_minutes": 20,
            "request_id": "req-test-reserve-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["item_id"] == "ITM-DORA01-001"
    assert payload["data"]["status"] == "active"


def test_inventory_reservation_item_not_available(client: TestClient) -> None:
    response = client.post(
        "/api/v1/inventory/reservations",
        json={
            "item_id": "ITM-OP105-002",
            "customer_id": 1,
            "reservation_minutes": 20,
            "request_id": "req-test-reserve-002",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ITEM_NOT_AVAILABLE"


def test_crm_upsert_success(client: TestClient) -> None:
    response = client.put(
        "/api/v1/customers/0901234567",
        json={
            "phone": "0901234567",
            "name": "Nguyen Thi Kim",
            "membership_level": "gold",
            "address": "District 1",
            "deposit_delta": 50000,
            "debt_delta": 0,
            "request_id": "req-test-crm-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["phone"] == "0901234567"
    assert payload["data"]["membership_level"] == "gold"


def test_crm_upsert_invalid_phone(client: TestClient) -> None:
    response = client.put(
        "/api/v1/customers/123abc789",
        json={
            "phone": "123abc789",
            "name": "Invalid Phone",
            "membership_level": "standard",
            "request_id": "req-test-crm-002",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_PHONE"
