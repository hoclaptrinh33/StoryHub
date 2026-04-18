from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["error"] is None
    assert payload["data"]["status"] == "ok"


def test_not_found_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/khong-ton-tai")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"]["code"] == "HTTP_404"
