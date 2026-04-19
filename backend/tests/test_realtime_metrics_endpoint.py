from __future__ import annotations

from fastapi.testclient import TestClient

from tests.auth_helpers import build_auth_headers


def test_realtime_metrics_endpoint_returns_snapshot_for_manager(client: TestClient) -> None:
    response = client.get(
        "/api/v1/system/realtime/metrics",
        headers=build_auth_headers("manager-demo"),
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["success"] is True
    data = payload["data"]
    assert data["ws_connections_active"] >= 0
    assert data["ws_connection_rejections_total"] >= 0
    assert "ws_events_published_total" in data
    assert "ws_event_latency_ms" in data
    assert "ws_broadcast_failures_total" in data
    assert data["generated_at"]
