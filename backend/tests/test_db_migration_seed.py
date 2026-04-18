import sqlite3
from pathlib import Path

import pytest

from app.db.migration import apply_schema_migration, resolve_sqlite_path, rollback_schema_migration
from app.db.seed import seed_database


def _build_database_url(tmp_path: Path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'storyhub-test.db'}"


def test_migration_up_and_down(tmp_path: Path) -> None:
    database_url = _build_database_url(tmp_path)
    database_path = resolve_sqlite_path(database_url)

    assert apply_schema_migration(database_url=database_url) is True
    assert database_path.exists()

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table';"
            ).fetchall()
        }

    assert "title" in tables
    assert "item" in tables
    assert "rental_contract" in tables

    assert rollback_schema_migration(database_url=database_url) is True

    with sqlite3.connect(database_path) as connection:
        tables_after_rollback = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table';"
            ).fetchall()
        }

    assert "title" not in tables_after_rollback
    assert "item" not in tables_after_rollback
    assert "schema_migrations" in tables_after_rollback


def test_seed_database_is_idempotent(tmp_path: Path) -> None:
    database_url = _build_database_url(tmp_path)

    apply_schema_migration(database_url=database_url)

    first_seed_counts = seed_database(database_url=database_url)
    second_seed_counts = seed_database(database_url=database_url)

    assert first_seed_counts == second_seed_counts
    assert first_seed_counts["title"] == 3
    assert first_seed_counts["customer"] == 3
    assert first_seed_counts["pos_order"] == 2
    assert first_seed_counts["rental_contract"] == 2


def test_seed_requires_migration(tmp_path: Path) -> None:
    database_url = _build_database_url(tmp_path)

    with pytest.raises(RuntimeError, match="Database schema is not ready"):
        seed_database(database_url=database_url)


def test_schema_constraints_and_indexes(tmp_path: Path) -> None:
    database_url = _build_database_url(tmp_path)
    database_path = resolve_sqlite_path(database_url)

    apply_schema_migration(database_url=database_url)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON;")

        connection.execute(
            """
            INSERT INTO title (name, author, publisher, genre, description, cover_url)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            ("Test Title", "Author", "Publisher", "Genre", "Description", None),
        )
        title_id = int(connection.execute("SELECT id FROM title LIMIT 1;").fetchone()["id"])

        connection.execute(
            """
            INSERT INTO volume (title_id, volume_number, isbn)
            VALUES (?, ?, ?);
            """,
            (title_id, 1, "isbn-test-1"),
        )
        volume_id = int(connection.execute("SELECT id FROM volume LIMIT 1;").fetchone()["id"])

        connection.execute(
            """
            INSERT INTO item (
                id,
                volume_id,
                condition_level,
                status,
                health_percent,
                notes,
                reserved_by_customer_id,
                reserved_at,
                reservation_expire_at,
                version_no
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                "VALID-ITEM-001",
                volume_id,
                100,
                "available",
                100,
                None,
                None,
                None,
                None,
                0,
            ),
        )

        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO item (
                    id,
                    volume_id,
                    condition_level,
                    status,
                    health_percent,
                    notes,
                    reserved_by_customer_id,
                    reserved_at,
                    reservation_expire_at,
                    version_no
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    "INVALID-ITEM-001",
                    volume_id,
                    100,
                    "wrong-status",
                    100,
                    None,
                    None,
                    None,
                    None,
                    0,
                ),
            )

        query_plan_rows = connection.execute(
            "EXPLAIN QUERY PLAN SELECT * FROM item WHERE status = 'available';"
        ).fetchall()

    assert any("idx_item_status" in row[3] for row in query_plan_rows)
