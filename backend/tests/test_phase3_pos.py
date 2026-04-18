from __future__ import annotations

from fastapi.testclient import TestClient


def _auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Device-Id": "TEST-KIOSK-01",
    }


def test_pos_create_order_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/checkout/unified",
        json={
            "customer_id": 1,
            "scanned_codes": ["9784088826001"],
            "discount_type": "none",
            "discount_value": 0,
            "split_payments": [{"method": "cash", "amount": 30000}],
            "request_id": "req-test-pos-create-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["order_id"] is not None
    assert payload["data"]["grand_total"] == 30000


def test_pos_create_order_split_mismatch(client: TestClient) -> None:
    response = client.post(
        "/api/v1/checkout/unified",
        json={
            "customer_id": 1,
            "scanned_codes": ["9784088826001"],
            "discount_type": "none",
            "discount_value": 0,
            "split_payments": [{"method": "cash", "amount": 1}],
            "request_id": "req-test-pos-create-002",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "PAYMENT_MISMATCH"


def test_pos_refund_requires_manager(client: TestClient) -> None:
    response = client.post(
        "/api/v1/pos/orders/1001/refund",
        json={
            "refund_items": [{"volume_id": 11, "quantity": 1}],
            "reason": "customer_request",
            "request_id": "req-test-pos-refund-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "AUTH_ROLE_DENIED"


def test_pos_refund_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/pos/orders/1001/refund",
        json={
            "refund_items": [{"volume_id": 11, "quantity": 1}],
            "reason": "customer_request",
            "request_id": "req-test-pos-refund-002",
        },
        headers=_auth_headers("manager-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["order_id"] == "1001"
    assert payload["data"]["order_status"] == "refunded"
