from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.db.migration import open_sqlite_connection
from app.services.cover_storage import resolve_runtime_root
from tests.auth_helpers import build_auth_headers


def _auth_headers(token: str) -> dict[str, str]:
    return build_auth_headers(token)


def _report_window() -> tuple[str, str]:
    now = datetime.now(UTC)
    from_date = (now - timedelta(days=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    to_date = (now + timedelta(days=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return from_date, to_date


def test_metadata_autofill_should_cache_after_first_lookup(client: TestClient) -> None:
    first = client.post(
        "/api/v1/metadata/autofill",
        json={
            "isbn": "9784088826001",
            "request_id": "req-meta-cache-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["success"] is True
    assert first_payload["data"]["metadata"]["name"]

    second = client.post(
        "/api/v1/metadata/autofill",
        json={
            "isbn": "9784088826001",
            "request_id": "req-meta-cache-002",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert second.status_code == 200
    second_payload = second.json()
    assert second_payload["success"] is True
    assert second_payload["data"]["source"] == "cache"
    assert second_payload["data"]["cache_hit"] is True


def test_metadata_autofill_invalid_query(client: TestClient) -> None:
    response = client.post(
        "/api/v1/metadata/autofill",
        json={
            "request_id": "req-meta-invalid-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_QUERY"


def test_report_revenue_summary_success(client: TestClient) -> None:
    from_date, to_date = _report_window()
    response = client.post(
        "/api/v1/reports/revenue-summary",
        json={
            "from_date": from_date,
            "to_date": to_date,
            "group_by": "day",
            "request_id": "req-report-001",
        },
        headers=_auth_headers("manager-demo"),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["sell_revenue"] == 40000
    assert payload["data"]["rental_revenue"] == 12000
    assert payload["data"]["penalty_revenue"] == 5000
    assert payload["data"]["total_revenue"] == 57000


def test_report_revenue_summary_invalid_range(client: TestClient) -> None:
    response = client.post(
        "/api/v1/reports/revenue-summary",
        json={
            "from_date": "2026-12-01T00:00:00Z",
            "to_date": "2026-01-01T00:00:00Z",
            "group_by": "day",
            "request_id": "req-report-invalid-range-001",
        },
        headers=_auth_headers("manager-demo"),
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "INVALID_DATE_RANGE"


def test_report_revenue_summary_requires_manager_or_owner(client: TestClient) -> None:
    from_date, to_date = _report_window()
    response = client.post(
        "/api/v1/reports/revenue-summary",
        json={
            "from_date": from_date,
            "to_date": to_date,
            "group_by": "day",
            "request_id": "req-report-auth-001",
        },
        headers=_auth_headers("cashier-demo"),
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "AUTH_ROLE_DENIED"


def test_system_backup_create_and_latest_status_and_restore_check(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/system/backups",
        json={
            "backup_type": "full",
            "request_id": "req-backup-create-001",
        },
        headers=_auth_headers("manager-demo"),
    )

    assert create_response.status_code == 200
    create_payload = create_response.json()
    assert create_payload["success"] is True
    assert create_payload["data"]["status"] == "success"
    assert create_payload["data"]["checksum"].startswith("sha256:")

    backup_file = resolve_runtime_root() / create_payload["data"]["file_path"]
    assert backup_file.exists()

    latest_response = client.get(
        "/api/v1/system/backups/latest",
        headers=_auth_headers("manager-demo"),
    )

    assert latest_response.status_code == 200
    latest_payload = latest_response.json()
    assert latest_payload["success"] is True
    assert latest_payload["data"]["backup_job_id"] == create_payload["data"]["backup_job_id"]
    assert latest_payload["data"]["status"] == "success"

    with sqlite3.connect(Path(backup_file)) as connection:
        title_count = connection.execute("SELECT COUNT(*) FROM title;").fetchone()[0]

    assert title_count >= 1


def test_system_backup_conflict_when_running_job_exists(client: TestClient) -> None:
    settings = get_settings()
    connection = open_sqlite_connection(settings.database_url)
    try:
        with connection:
            connection.execute(
                """
                INSERT INTO backup_job (
                    backup_type,
                    status,
                    file_path,
                    checksum,
                    error_message,
                    started_at,
                    finished_at,
                    created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "full",
                    "running",
                    "pending",
                    None,
                    None,
                    "2026-01-01T00:00:00Z",
                    None,
                    "system",
                ),
            )
    finally:
        connection.close()

    conflict_response = client.post(
        "/api/v1/system/backups",
        json={
            "backup_type": "incremental",
            "request_id": "req-backup-conflict-001",
        },
        headers=_auth_headers("manager-demo"),
    )

    assert conflict_response.status_code == 409
    conflict_payload = conflict_response.json()
    assert conflict_payload["success"] is False
    assert conflict_payload["error"]["code"] == "BACKUP_ALREADY_RUNNING"
