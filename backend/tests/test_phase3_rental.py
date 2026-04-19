from __future__ import annotations

from fastapi.testclient import TestClient

from tests.auth_helpers import build_auth_headers


def _auth_headers(token: str) -> dict[str, str]:
    return build_auth_headers(token)


def test_rental_create_contract_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/rentals/contracts",
        json={
            "customer_id": 1,
            "item_ids": ["ITM-DORA01-001"],
            "due_date": "2030-04-25T10:00:00Z",
            "deposit_policy": "auto",
            "request_id": "req-test-rental-create-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["customer_id"] == "1"
    assert payload["data"]["rental_items"][0]["status"] == "rented"


def test_rental_extend_invalid_due_date(client: TestClient) -> None:
    response = client.post(
        "/api/v1/rentals/contracts/2001/extend",
        json={
            "new_due_date": "2020-01-01T00:00:00Z",
            "request_id": "req-test-rental-extend-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_DUE_DATE"


def test_rental_return_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/rentals/contracts/2001/return",
        json={
            "return_lines": [{"item_id": "ITM-CON98-001", "condition_after": "good"}],
            "request_id": "req-test-rental-return-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["contract_id"] == "2001"
    assert payload["data"]["contract_status"] == "closed"


def test_rental_return_item_not_in_contract(client: TestClient) -> None:
    response = client.post(
        "/api/v1/rentals/contracts/2001/return",
        json={
            "return_lines": [{"item_id": "ITM-DORA01-001", "condition_after": "good"}],
            "request_id": "req-test-rental-return-002",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "ITEM_NOT_IN_CONTRACT"


def test_rental_get_contract_preview_success(client: TestClient) -> None:
    response = client.get(
        "/api/v1/rentals/contracts/2001",
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["contract_id"] == "2001"
    assert payload["data"]["customer_name"] == "Tran Thi Binh"
    assert payload["data"]["remaining_deposit"] == 80000
    assert len(payload["data"]["return_lines"]) == 1
    assert payload["data"]["return_lines"][0]["item_id"] == "ITM-CON98-001"


def test_rental_list_returnable_contracts_success(client: TestClient) -> None:
    response = client.get(
        "/api/v1/rentals/contracts",
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert isinstance(payload["data"], list)
    contract = next((item for item in payload["data"] if item["contract_id"] == "2001"), None)
    assert contract is not None
    assert contract["open_item_count"] == 1
    assert "Detective Conan" in contract["rented_items_preview"]


def test_rental_list_returnable_contracts_search_by_phone(client: TestClient) -> None:
    response = client.get(
        "/api/v1/rentals/contracts?q=0900000002",
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]) == 1
    assert payload["data"][0]["contract_id"] == "2001"
    assert payload["data"][0]["customer_name"] == "Tran Thi Binh"


def test_rental_get_contract_preview_closed_contract(client: TestClient) -> None:
    response = client.get(
        "/api/v1/rentals/contracts/2002",
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "CONTRACT_NOT_RETURNABLE"
