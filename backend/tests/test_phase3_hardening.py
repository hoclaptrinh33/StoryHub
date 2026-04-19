from __future__ import annotations

from fastapi.testclient import TestClient

from tests.auth_helpers import build_auth_headers


def _auth_headers(token: str | None) -> dict[str, str]:
    return build_auth_headers(token)


def test_auth_missing_token_inventory(client: TestClient) -> None:
    response = client.post(
        "/api/v1/inventory/reservations",
        json={
            "item_id": "ITM-DORA01-001",
            "customer_id": 1,
            "reservation_minutes": 20,
            "request_id": "req-auth-fallback-001",
        },
        headers=_auth_headers(None),
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "AUTH_MISSING_TOKEN"


def test_auth_invalid_token_inventory(client: TestClient) -> None:
    response = client.post(
        "/api/v1/inventory/reservations",
        json={
            "item_id": "ITM-DORA01-001",
            "customer_id": 1,
            "reservation_minutes": 20,
            "request_id": "req-auth-invalid-001",
        },
        headers=_auth_headers("unknown-token"),
    )

    assert response.status_code == 401
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "AUTH_INVALID_TOKEN"


def test_inventory_reservation_idempotency_replay(client: TestClient) -> None:
    request_body = {
        "item_id": "ITM-DORA01-001",
        "customer_id": 1,
        "reservation_minutes": 20,
        "request_id": "req-idem-inventory-001",
    }

    first = client.post(
        "/api/v1/inventory/reservations",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )
    second = client.post(
        "/api/v1/inventory/reservations",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_crm_upsert_idempotency_replay(client: TestClient) -> None:
    request_body = {
        "phone": "0901234567",
        "name": "Nguyen Thi Kim",
        "membership_level": "gold",
        "address": "District 1",
        "deposit_delta": 50000,
        "debt_delta": 0,
        "request_id": "req-idem-crm-001",
    }

    first = client.put(
        "/api/v1/customers/0901234567",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )
    second = client.put(
        "/api/v1/customers/0901234567",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_pos_create_idempotency_replay(client: TestClient) -> None:
    request_body = {
        "customer_id": 1,
        "scanned_codes": ["9784088826001"],
        "discount_type": "none",
        "discount_value": 0,
        "split_payments": [{"method": "cash", "amount": 30000}],
        "request_id": "req-idem-pos-create-001",
    }

    first = client.post(
        "/api/v1/checkout/unified",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )
    second = client.post(
        "/api/v1/checkout/unified",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_pos_refund_duplicate_blocked_by_business_rule(client: TestClient) -> None:
    first = client.post(
        "/api/v1/pos/orders/1001/refund",
        json={
            "refund_items": [{"volume_id": 11, "quantity": 1}],
            "reason": "duplicate-check",
            "request_id": "req-refund-business-001",
        },
        headers=_auth_headers("manager-demo"),
    )
    second = client.post(
        "/api/v1/pos/orders/1001/refund",
        json={
            "refund_items": [{"volume_id": 11, "quantity": 1}],
            "reason": "duplicate-check",
            "request_id": "req-refund-business-002",
        },
        headers=_auth_headers("manager-demo"),
    )

    assert first.status_code == 200
    assert second.status_code == 409
    payload = second.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ITEM_ALREADY_REFUNDED"


def test_pos_refund_idempotency_replay(client: TestClient) -> None:
    request_body = {
        "refund_items": [{"volume_id": 11, "quantity": 1}],
        "reason": "same-request",
        "request_id": "req-idem-pos-refund-001",
    }

    first = client.post(
        "/api/v1/pos/orders/1001/refund",
        json=request_body,
        headers=_auth_headers("manager-demo"),
    )
    second = client.post(
        "/api/v1/pos/orders/1001/refund",
        json=request_body,
        headers=_auth_headers("manager-demo"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_rental_create_contract_idempotency_replay(client: TestClient) -> None:
    request_body = {
        "customer_id": 1,
        "item_ids": ["ITM-DORA01-001"],
        "due_date": "2030-04-25T10:00:00Z",
        "deposit_policy": "auto",
        "request_id": "req-idem-rental-create-001",
    }

    first = client.post(
        "/api/v1/rentals/contracts",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )
    second = client.post(
        "/api/v1/rentals/contracts",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()


def test_rental_return_duplicate_blocked_by_business_rule(client: TestClient) -> None:
    first = client.post(
        "/api/v1/rentals/contracts/2001/return",
        json={
            "return_lines": [{"item_id": "ITM-CON98-001", "condition_after": "good"}],
            "request_id": "req-return-business-001",
        },
        headers=_auth_headers("cashier-demo"),
    )
    second = client.post(
        "/api/v1/rentals/contracts/2001/return",
        json={
            "return_lines": [{"item_id": "ITM-CON98-001", "condition_after": "good"}],
            "request_id": "req-return-business-002",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert first.status_code == 200
    assert second.status_code == 404
    payload = second.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "CONTRACT_NOT_FOUND"


def test_rental_return_idempotency_replay(client: TestClient) -> None:
    request_body = {
        "return_lines": [{"item_id": "ITM-CON98-001", "condition_after": "good"}],
        "request_id": "req-idem-rental-return-001",
    }

    first = client.post(
        "/api/v1/rentals/contracts/2001/return",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )
    second = client.post(
        "/api/v1/rentals/contracts/2001/return",
        json=request_body,
        headers=_auth_headers("cashier-demo"),
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
