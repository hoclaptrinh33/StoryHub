from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints import checkout as checkout_endpoint
from app.core.config import get_settings
from app.db.migration import open_sqlite_connection
from tests.auth_helpers import build_auth_headers


def _auth_headers(token: str) -> dict[str, str]:
    return build_auth_headers(token)


def _db_execute(sql: str, params: tuple[object, ...] = ()) -> None:
    settings = get_settings()
    connection = open_sqlite_connection(settings.database_url)
    try:
        with connection:
            connection.execute(sql, params)
    finally:
        connection.close()


def _db_fetch_one(sql: str, params: tuple[object, ...] = ()) -> dict[str, object] | None:
    settings = get_settings()
    connection = open_sqlite_connection(settings.database_url)
    try:
        row = connection.execute(sql, params).fetchone()
        return dict(row) if row is not None else None
    finally:
        connection.close()


def _db_fetch_value(sql: str, params: tuple[object, ...] = ()) -> int:
    settings = get_settings()
    connection = open_sqlite_connection(settings.database_url)
    try:
        value = connection.execute(sql, params).fetchone()[0]
        return int(value or 0)
    finally:
        connection.close()


def _seed_checkout_price_rule_for_tests() -> None:
    _db_execute("UPDATE price_rule SET status = 'retired', updated_at = CURRENT_TIMESTAMP;")
    _db_execute(
        """
        UPDATE price_rule
        SET
            version_no = 101,
            status = 'active',
            k_rent = 0.02,
            k_deposit = 0.8,
            d_floor = 1000,
            used_demand_factor = 1.0,
            used_cap_ratio = 1.0,
            valid_from = NULL,
            valid_to = NULL,
            activated_by_user_id = 'system',
            note = 'test price rule',
            updated_at = CURRENT_TIMESTAMP,
            activated_at = CURRENT_TIMESTAMP
        WHERE id = 1;
        """
    )


def test_rental_emergency_refund_should_rollback_full_contract(client: TestClient) -> None:
    response = client.post(
        "/api/v1/system/transactions/rental/2001/emergency-refund",
        json={
            "reason": "Thu ngan lap sai hop dong",
            "request_id": "req-rental-emergency-001",
            "refund_method": "cash",
        },
        headers=_auth_headers("owner-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["contract_id"] == "2001"
    assert payload["data"]["contract_status"] == "cancelled"
    assert payload["data"]["refunded_total"] == 95000

    contract_row = _db_fetch_one(
        "SELECT status, remaining_deposit, debt_total FROM rental_contract WHERE id = ?",
        (2001,),
    )
    assert contract_row is not None
    assert contract_row["status"] == "cancelled"
    assert int(contract_row["remaining_deposit"]) == 0
    assert int(contract_row["debt_total"]) == 0

    item_row = _db_fetch_one("SELECT status FROM item WHERE id = ?", ("ITM-CON98-001",))
    assert item_row is not None
    assert item_row["status"] == "available"

    refund_row = _db_fetch_one(
        "SELECT reason, refund_method, refunded_total FROM rental_refund WHERE contract_id = ?",
        (2001,),
    )
    assert refund_row is not None
    assert refund_row["reason"] == "Thu ngan lap sai hop dong"
    assert refund_row["refund_method"] == "cash"
    assert int(refund_row["refunded_total"]) == 95000

    refund_item_count = _db_fetch_value(
        """
        SELECT COUNT(*)
        FROM rental_refund_item
        WHERE refund_id = (SELECT id FROM rental_refund WHERE contract_id = ?)
        """,
        (2001,),
    )
    assert refund_item_count == 1


def test_rental_emergency_refund_should_be_idempotent_by_request_id(client: TestClient) -> None:
    request_payload = {
        "reason": "Hoan tien khan cap do sai thao tac",
        "request_id": "req-rental-emergency-002",
        "refund_method": "original_method",
    }

    first_response = client.post(
        "/api/v1/system/transactions/rental/2001/emergency-refund",
        json=request_payload,
        headers=_auth_headers("owner-demo"),
    )
    second_response = client.post(
        "/api/v1/system/transactions/rental/2001/emergency-refund",
        json=request_payload,
        headers=_auth_headers("owner-demo"),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_payload = first_response.json()
    second_payload = second_response.json()
    assert first_payload["success"] is True
    assert second_payload["success"] is True
    assert first_payload["data"]["refund_id"] == second_payload["data"]["refund_id"]
    assert first_payload["data"]["contract_id"] == second_payload["data"]["contract_id"]

    refund_count = _db_fetch_value(
        "SELECT COUNT(*) FROM rental_refund WHERE request_id = ?",
        ("req-rental-emergency-002",),
    )
    assert refund_count == 1


def test_rental_emergency_refund_should_fail_when_contract_not_found(client: TestClient) -> None:
    response = client.post(
        "/api/v1/system/transactions/rental/999999/emergency-refund",
        json={
            "reason": "Not found case",
            "request_id": "req-rental-emergency-404",
            "refund_method": "cash",
        },
        headers=_auth_headers("owner-demo"),
    )

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "CONTRACT_NOT_FOUND"


def test_patch_auto_promotion_should_update_full_fields(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/promotions/auto-promotions",
        json={
            "name": "Tue Promo",
            "day_of_week": 1,
            "discount_percent": 20,
        },
        headers=_auth_headers("owner-demo"),
    )
    assert create_response.status_code == 200
    promo_id = int(create_response.json()["data"]["id"])

    update_response = client.patch(
        f"/api/v1/promotions/auto-promotions/{promo_id}",
        json={
            "name": "Midweek Promo",
            "day_of_week": 2,
            "discount_percent": 25,
            "is_active": False,
        },
        headers=_auth_headers("owner-demo"),
    )

    assert update_response.status_code == 200
    update_payload = update_response.json()
    assert update_payload["success"] is True
    assert update_payload["data"]["status"] == "updated"

    promo_row = _db_fetch_one(
        """
        SELECT name, day_of_week, discount_percent, is_active
        FROM automatic_promotion
        WHERE id = ?
        """,
        (promo_id,),
    )
    assert promo_row is not None
    assert promo_row["name"] == "Midweek Promo"
    assert int(promo_row["day_of_week"]) == 2
    assert int(promo_row["discount_percent"]) == 25
    assert int(promo_row["is_active"]) == 0

    audit_count = _db_fetch_value(
        """
        SELECT COUNT(*)
        FROM audit_log
        WHERE action = 'AUTO_PROMO_UPDATED'
          AND entity_type = 'automatic_promotion'
          AND entity_id = ?
        """,
        (str(promo_id),),
    )
    assert audit_count == 1


def test_patch_auto_promotion_should_reject_empty_payload(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/promotions/auto-promotions",
        json={
            "name": "Tue Promo",
            "day_of_week": 1,
            "discount_percent": 20,
        },
        headers=_auth_headers("owner-demo"),
    )
    assert create_response.status_code == 200
    promo_id = int(create_response.json()["data"]["id"])

    update_response = client.patch(
        f"/api/v1/promotions/auto-promotions/{promo_id}",
        json={},
        headers=_auth_headers("owner-demo"),
    )
    assert update_response.status_code == 400
    update_payload = update_response.json()
    assert update_payload["success"] is False
    assert update_payload["error"]["code"] == "NO_CHANGES"


def test_checkout_unified_should_apply_auto_promo_for_rental_on_matching_day(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_now = datetime(2026, 4, 21, 8, 0, tzinfo=UTC)  # Tue
    monkeypatch.setattr(checkout_endpoint, "utc_now", lambda: fixed_now)
    _seed_checkout_price_rule_for_tests()

    _db_execute(
        """
        INSERT INTO automatic_promotion (name, day_of_week, discount_percent, is_active)
        VALUES (?, ?, ?, 1);
        """,
        ("Tuesday Rental 20%", fixed_now.weekday(), 20),
    )

    response = client.post(
        "/api/v1/checkout/unified",
        json={
            "customer_id": 1,
            "scanned_codes": ["ITM-DORA01-001"],
            "discount_type": "none",
            "discount_value": 0,
            "split_payments": [{"method": "cash", "amount": 21600}],
            "request_id": "req-checkout-auto-promo-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["total_rentals"] == 1600
    assert data["total_deposit"] == 20000
    assert data["grand_total"] == 21600
    assert data["price_rule_version"] == 101
    assert data["auto_promo_discount_total"] == 400
    assert data["auto_promo_name"] == "Tuesday Rental 20%"

    contract_id = int(data["rental_contract_id"])
    rental_row = _db_fetch_one(
        "SELECT final_rent_price FROM rental_item WHERE contract_id = ?",
        (contract_id,),
    )
    assert rental_row is not None
    assert int(rental_row["final_rent_price"]) == 1600


def test_checkout_unified_should_not_apply_auto_promo_on_other_day(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixed_now = datetime(2026, 4, 22, 8, 0, tzinfo=UTC)  # Wed
    monkeypatch.setattr(checkout_endpoint, "utc_now", lambda: fixed_now)
    _seed_checkout_price_rule_for_tests()

    _db_execute(
        """
        INSERT INTO automatic_promotion (name, day_of_week, discount_percent, is_active)
        VALUES (?, ?, ?, 1);
        """,
        ("Tuesday Rental 20%", 1, 20),
    )

    response = client.post(
        "/api/v1/checkout/unified",
        json={
            "customer_id": 1,
            "scanned_codes": ["ITM-DORA01-001"],
            "discount_type": "none",
            "discount_value": 0,
            "split_payments": [{"method": "cash", "amount": 22000}],
            "request_id": "req-checkout-auto-promo-002",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["total_rentals"] == 2000
    assert data["total_deposit"] == 20000
    assert data["grand_total"] == 22000
    assert data["price_rule_version"] == 101
    assert data["auto_promo_discount_total"] == 0
    assert data["auto_promo_id"] is None
