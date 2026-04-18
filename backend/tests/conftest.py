from __future__ import annotations

import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import get_settings
from app.db.migration import apply_schema_migration, open_sqlite_connection
from app.db.runtime_schema import ensure_runtime_tables
from app.db.seed import seed_database
from app.db.session import engine
from app.main import app

_SEED_RESET_ORDER = (
    "audit_log",
    "backup_job",
    "metadata_cache",
    "rental_settlement",
    "rental_item",
    "rental_contract",
    "pos_payment",
    "pos_order_item",
    "pos_order",
    "reservation",
    "item",
    "customer",
    "volume",
    "title",
)


async def _reset_runtime_tables() -> None:
    await ensure_runtime_tables()
    async with engine.begin() as connection:
        await connection.execute(text("DELETE FROM pos_refund_item;"))
        await connection.execute(text("DELETE FROM pos_refund;"))
        await connection.execute(text("DELETE FROM idempotency_record;"))


def _reset_seed_tables(database_url: str) -> None:
    connection = open_sqlite_connection(database_url)
    try:
        with connection:
            for table_name in _SEED_RESET_ORDER:
                connection.execute(f"DELETE FROM {table_name};")
    finally:
        connection.close()


@pytest.fixture(autouse=True)
def reset_database_state() -> None:
    settings = get_settings()
    apply_schema_migration(database_url=settings.database_url)
    asyncio.run(_reset_runtime_tables())
    _reset_seed_tables(settings.database_url)
    seed_database(database_url=settings.database_url)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def auth_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Request-Id": "test-header-request-id",
        "X-Device-Id": "TEST-KIOSK-01",
    }
