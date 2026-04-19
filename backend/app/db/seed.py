from __future__ import annotations

import argparse
import json
import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from app.db.migration import open_sqlite_connection, resolve_database_url, resolve_sqlite_path

_SEED_TABLES = (
    "title",
    "volume",
    "price_rule",
    "customer",
    "item",
    "reservation",
    "pos_order",
    "pos_order_item",
    "pos_payment",
    "rental_contract",
    "rental_item",
    "order_item",
    "rental_settlement",
    "metadata_cache",
    "backup_job",
    "audit_log",
)


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _ensure_schema_ready(connection: sqlite3.Connection) -> None:
    cursor = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
    available_tables = {row["name"] for row in cursor.fetchall()}

    missing_tables = [
        table_name for table_name in _SEED_TABLES if table_name not in available_tables
    ]
    if missing_tables:
        missing = ", ".join(missing_tables)
        raise RuntimeError(
            "Database schema is not ready for seeding. "
            f"Missing tables: {missing}. Run migration first."
        )


def _upsert_rows(
    connection: sqlite3.Connection,
    table_name: str,
    columns: Sequence[str],
    primary_keys: Sequence[str],
    rows: Sequence[tuple[object, ...]],
) -> None:
    if not rows:
        return

    column_clause = ", ".join(columns)
    placeholders = ", ".join("?" for _ in columns)
    conflict_clause = ", ".join(primary_keys)

    update_columns = [column for column in columns if column not in primary_keys]
    if update_columns:
        update_clause = ", ".join(f"{column} = excluded.{column}" for column in update_columns)
        sql = (
            f"INSERT INTO {table_name} ({column_clause}) VALUES ({placeholders}) "
            f"ON CONFLICT({conflict_clause}) DO UPDATE SET {update_clause};"
        )
    else:
        sql = (
            f"INSERT INTO {table_name} ({column_clause}) VALUES ({placeholders}) "
            f"ON CONFLICT({conflict_clause}) DO NOTHING;"
        )

    connection.executemany(sql, rows)


def _collect_counts(connection: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table_name in _SEED_TABLES:
        cursor = connection.execute(f"SELECT COUNT(*) AS total FROM {table_name};")
        counts[table_name] = int(cursor.fetchone()["total"])
    return counts


def seed_database(database_url: str | None = None) -> dict[str, int]:
    resolved_url = resolve_database_url(database_url)
    connection = open_sqlite_connection(resolved_url)

    try:
        _ensure_schema_ready(connection)

        now = datetime.now(UTC)
        now_iso = _iso(now)
        rental_due_iso = _iso(now + timedelta(days=3))
        reservation_expire_iso = _iso(now + timedelta(minutes=30))
        cache_expire_iso = _iso(now + timedelta(days=30))
        closed_rent_date_iso = _iso(now - timedelta(days=7))
        closed_due_date_iso = _iso(now - timedelta(days=2))

        title_rows = [
            (
                1,
                "One Piece",
                "Eiichiro Oda",
                "Shueisha",
                "Shonen",
                "Pirate adventure",
                None,
                now_iso,
                now_iso,
                None,
            ),
            (
                2,
                "Detective Conan",
                "Gosho Aoyama",
                "Shogakukan",
                "Mystery",
                "Detective stories",
                None,
                now_iso,
                now_iso,
                None,
            ),
            (
                3,
                "Doraemon",
                "Fujiko F. Fujio",
                "Shogakukan",
                "Kids",
                "Classic robot cat manga",
                None,
                now_iso,
                now_iso,
                None,
            ),
        ]

        volume_rows = [
            (11, 1, 105, "9784088826001", 5, 30000, now_iso, now_iso, None),
            (12, 1, 106, "9784088826018", 2, 32000, now_iso, now_iso, None),
            (21, 2, 98, "9784098503213", 10, 28000, now_iso, now_iso, None),
            (22, 2, 99, "9784098503220", 0, 28000, now_iso, now_iso, None),
            (31, 3, 1, None, 1, 25000, now_iso, now_iso, None),
        ]

        price_rule_rows = [
            (
                1,
                "default",
                1,
                "active",
                0.2666666667,
                1.0666666667,
                10000,
                1.0,
                1.0,
                now_iso,
                None,
                "system",
                "system",
                "Default active pricing rule",
                now_iso,
                now_iso,
                now_iso,
            ),
            (
                2,
                "default",
                2,
                "draft",
                0.28,
                1.1,
                12000,
                1.0,
                0.95,
                None,
                None,
                "manager-01",
                None,
                "Draft pricing rule for manager review",
                now_iso,
                now_iso,
                None,
            ),
        ]

        customer_rows = [
            (
                1,
                "Nguyen Van An",
                "0900000001",
                "District 1",
                "vip",
                500000,
                0,
                0,
                now_iso,
                now_iso,
                None,
            ),
            (
                2,
                "Tran Thi Binh",
                "0900000002",
                "District 3",
                "regular",
                300000,
                0,
                0,
                now_iso,
                now_iso,
                None,
            ),
            (
                3,
                "Le Minh Chau",
                "0900000003",
                "District 7",
                "regular",
                0,
                0,
                0,
                now_iso,
                now_iso,
                None,
            ),
        ]

        item_rows = [
            (
                "ITM-OP105-001",
                11,
                100,
                "available",
                100,
                None,
                None,
                None,
                None,
                0,
                now_iso,
                now_iso,
                None,
            ),
            (
                "ITM-OP105-002",
                11,
                95,
                "lost",
                95,
                None,
                None,
                None,
                None,
                0,
                now_iso,
                now_iso,
                None,
            ),
            (
                "ITM-CON98-001",
                21,
                90,
                "rented",
                90,
                None,
                None,
                None,
                None,
                0,
                now_iso,
                now_iso,
                None,
            ),
            (
                "ITM-CON99-001",
                22,
                88,
                "reserved",
                88,
                "Reserved for customer",
                2,
                now_iso,
                reservation_expire_iso,
                1,
                now_iso,
                now_iso,
                None,
            ),
            (
                "ITM-DORA01-001",
                31,
                100,
                "available",
                100,
                None,
                None,
                None,
                None,
                0,
                now_iso,
                now_iso,
                None,
            ),
            (
                "ITM-DORA01-002",
                31,
                95,
                "available",
                95,
                None,
                None,
                None,
                None,
                0,
                now_iso,
                now_iso,
                None,
            ),
        ]

        reservation_rows = [
            (
                3001,
                "ITM-CON99-001",
                2,
                "active",
                now_iso,
                reservation_expire_iso,
                None,
                "system",
            )
        ]

        pos_order_rows = [
            (
                1001,
                1,
                "paid",
                45000,
                "amount",
                5000,
                5000,
                40000,
                40000,
                "req-pos-1001",
                "cashier-01",
                now_iso,
                now_iso,
                None,
            ),
            (
                1002,
                None,
                "cancelled",
                30000,
                "none",
                0,
                0,
                30000,
                0,
                "req-pos-1002",
                "cashier-01",
                now_iso,
                now_iso,
                None,
            ),
        ]

        pos_order_item_rows = [
            (5001, 1001, 11, 40000, 1, 40000),
            (5002, 1002, 31, 30000, 1, 30000),
        ]

        pos_payment_rows = [(7001, 1001, "cash", 40000, now_iso)]

        rental_contract_rows = [
            (
                2001,
                2,
                "active",
                now_iso,
                rental_due_iso,
                80000,
                80000,
                0,
                "req-rental-2001",
                "cashier-02",
                now_iso,
                now_iso,
                None,
            ),
            (
                2002,
                3,
                "closed",
                closed_rent_date_iso,
                closed_due_date_iso,
                60000,
                43000,
                0,
                "req-rental-2002",
                "cashier-03",
                now_iso,
                now_iso,
                None,
            ),
        ]

        rental_item_rows = [
            (8001, 2001, "ITM-CON98-001", 15000, 80000, "rented", 90, None),
            (8002, 2002, "ITM-DORA01-002", 12000, 60000, "returned", 100, 95),
        ]

        order_item_rows = [
            (
                9901,
                "sale",
                1001,
                None,
                5001,
                None,
                11,
                None,
                1,
                30000,
                None,
                None,
                None,
                40000,
                None,
                None,
                40000,
                1,
                1,
                0,
                None,
                None,
                None,
                None,
                now_iso,
            ),
            (
                9902,
                "sale",
                1002,
                None,
                5002,
                None,
                31,
                None,
                1,
                25000,
                None,
                None,
                None,
                30000,
                None,
                None,
                30000,
                1,
                1,
                0,
                None,
                None,
                None,
                None,
                now_iso,
            ),
            (
                9903,
                "rental",
                None,
                2001,
                None,
                8001,
                21,
                "ITM-CON98-001",
                1,
                28000,
                0.2666666667,
                1.0666666667,
                10000,
                None,
                15000,
                80000,
                95000,
                1,
                1,
                0,
                None,
                None,
                None,
                None,
                now_iso,
            ),
            (
                9904,
                "rental",
                None,
                2002,
                None,
                8002,
                31,
                "ITM-DORA01-002",
                1,
                25000,
                0.2666666667,
                1.0666666667,
                10000,
                None,
                12000,
                60000,
                72000,
                1,
                1,
                0,
                None,
                None,
                None,
                None,
                now_iso,
            ),
        ]

        rental_settlement_rows = [
            (9001, 2002, 12000, 2000, 3000, 0, 17000, 17000, 43000, 0, now_iso)
        ]

        metadata_rows = [
            (
                9501,
                "barcode:ITM-OP105-001",
                "openlibrary",
                json.dumps({"title": "One Piece", "volume": 105}),
                0.92,
                now_iso,
                cache_expire_iso,
            )
        ]

        backup_rows = [
            (
                9601,
                "full",
                "success",
                "backups/storyhub-full.db",
                "sha256:demo-checksum",
                None,
                now_iso,
                now_iso,
                "system",
            )
        ]

        audit_rows = [
            (
                9701,
                "cashier-01",
                "ORDER_PAID",
                "pos_order",
                "1001",
                json.dumps({"status": "draft"}),
                json.dumps({"status": "paid"}),
                "127.0.0.1",
                "KIOSK-01",
                now_iso,
            ),
            (
                9702,
                "system",
                "RESERVATION_CREATED",
                "reservation",
                "3001",
                None,
                json.dumps({"status": "active"}),
                "127.0.0.1",
                "KIOSK-01",
                now_iso,
            ),
        ]

        with connection:
            _upsert_rows(
                connection,
                table_name="title",
                columns=(
                    "id",
                    "name",
                    "author",
                    "publisher",
                    "genre",
                    "description",
                    "cover_url",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
                primary_keys=("id",),
                rows=title_rows,
            )
            _upsert_rows(
                connection,
                table_name="volume",
                columns=(
                    "id",
                    "title_id",
                    "volume_number",
                    "isbn",
                    "retail_stock",
                    "p_sell_new",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
                primary_keys=("id",),
                rows=volume_rows,
            )
            _upsert_rows(
                connection,
                table_name="price_rule",
                columns=(
                    "id",
                    "rule_code",
                    "version_no",
                    "status",
                    "k_rent",
                    "k_deposit",
                    "d_floor",
                    "used_demand_factor",
                    "used_cap_ratio",
                    "valid_from",
                    "valid_to",
                    "created_by_user_id",
                    "activated_by_user_id",
                    "note",
                    "created_at",
                    "updated_at",
                    "activated_at",
                ),
                primary_keys=("id",),
                rows=price_rule_rows,
            )
            _upsert_rows(
                connection,
                table_name="customer",
                columns=(
                    "id",
                    "name",
                    "phone",
                    "address",
                    "membership_level",
                    "deposit_balance",
                    "debt",
                    "blacklist_flag",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
                primary_keys=("id",),
                rows=customer_rows,
            )
            _upsert_rows(
                connection,
                table_name="item",
                columns=(
                    "id",
                    "volume_id",
                    "condition_level",
                    "status",
                    "health_percent",
                    "notes",
                    "reserved_by_customer_id",
                    "reserved_at",
                    "reservation_expire_at",
                    "version_no",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
                primary_keys=("id",),
                rows=item_rows,
            )
            _upsert_rows(
                connection,
                table_name="reservation",
                columns=(
                    "id",
                    "item_id",
                    "customer_id",
                    "status",
                    "reserved_at",
                    "expire_at",
                    "converted_to",
                    "created_by_user_id",
                ),
                primary_keys=("id",),
                rows=reservation_rows,
            )
            _upsert_rows(
                connection,
                table_name="pos_order",
                columns=(
                    "id",
                    "customer_id",
                    "status",
                    "subtotal",
                    "discount_type",
                    "discount_value",
                    "discount_total",
                    "grand_total",
                    "paid_total",
                    "request_id",
                    "created_by_user_id",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
                primary_keys=("id",),
                rows=pos_order_rows,
            )
            _upsert_rows(
                connection,
                table_name="pos_order_item",
                columns=(
                    "id",
                    "order_id",
                    "volume_id",
                    "final_sell_price",
                    "quantity",
                    "line_total",
                ),
                primary_keys=("id",),
                rows=pos_order_item_rows,
            )
            _upsert_rows(
                connection,
                table_name="pos_payment",
                columns=("id", "order_id", "method", "amount", "paid_at"),
                primary_keys=("id",),
                rows=pos_payment_rows,
            )
            _upsert_rows(
                connection,
                table_name="rental_contract",
                columns=(
                    "id",
                    "customer_id",
                    "status",
                    "rent_date",
                    "due_date",
                    "deposit_total",
                    "remaining_deposit",
                    "debt_total",
                    "request_id",
                    "created_by_user_id",
                    "created_at",
                    "updated_at",
                    "deleted_at",
                ),
                primary_keys=("id",),
                rows=rental_contract_rows,
            )
            _upsert_rows(
                connection,
                table_name="rental_item",
                columns=(
                    "id",
                    "contract_id",
                    "item_id",
                    "final_rent_price",
                    "final_deposit",
                    "status",
                    "condition_before",
                    "condition_after",
                ),
                primary_keys=("id",),
                rows=rental_item_rows,
            )
            _upsert_rows(
                connection,
                table_name="order_item",
                columns=(
                    "id",
                    "order_type",
                    "pos_order_id",
                    "rental_contract_id",
                    "pos_order_item_id",
                    "rental_item_id",
                    "volume_id",
                    "item_id",
                    "quantity",
                    "p_sell_new_snapshot",
                    "rent_ratio_snapshot",
                    "deposit_ratio_snapshot",
                    "deposit_floor_snapshot",
                    "final_sell_price",
                    "final_rent_price",
                    "final_deposit",
                    "line_total",
                    "price_rule_id",
                    "price_rule_version",
                    "override_applied",
                    "override_reason_code",
                    "override_reason_note",
                    "approved_by_user_id",
                    "approved_via",
                    "created_at",
                ),
                primary_keys=("id",),
                rows=order_item_rows,
            )
            _upsert_rows(
                connection,
                table_name="rental_settlement",
                columns=(
                    "id",
                    "contract_id",
                    "rental_fee",
                    "late_fee",
                    "damage_fee",
                    "lost_fee",
                    "total_fee",
                    "deducted_from_deposit",
                    "refund_to_customer",
                    "remaining_debt",
                    "settled_at",
                ),
                primary_keys=("id",),
                rows=rental_settlement_rows,
            )
            _upsert_rows(
                connection,
                table_name="metadata_cache",
                columns=(
                    "id",
                    "query_key",
                    "source",
                    "payload_json",
                    "confidence",
                    "cached_at",
                    "expire_at",
                ),
                primary_keys=("id",),
                rows=metadata_rows,
            )
            _upsert_rows(
                connection,
                table_name="backup_job",
                columns=(
                    "id",
                    "backup_type",
                    "status",
                    "file_path",
                    "checksum",
                    "error_message",
                    "started_at",
                    "finished_at",
                    "created_by_user_id",
                ),
                primary_keys=("id",),
                rows=backup_rows,
            )
            _upsert_rows(
                connection,
                table_name="audit_log",
                columns=(
                    "id",
                    "actor_user_id",
                    "action",
                    "entity_type",
                    "entity_id",
                    "before_json",
                    "after_json",
                    "ip_address",
                    "device_id",
                    "created_at",
                ),
                primary_keys=("id",),
                rows=audit_rows,
            )

        return _collect_counts(connection)
    finally:
        connection.close()


def run_cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="StoryHub SQLite seed runner")
    parser.add_argument(
        "--database-url",
        dest="database_url",
        default=None,
        help="Override STORYHUB_DATABASE_URL.",
    )
    args = parser.parse_args(argv)

    try:
        database_url = resolve_database_url(args.database_url)
        database_path = resolve_sqlite_path(database_url)
        counts = seed_database(database_url=database_url)

        print(f"database: {database_path}")
        for table_name in _SEED_TABLES:
            print(f"{table_name}: {counts[table_name]}")
        return 0
    except Exception as exc:
        print(f"Seed command failed: {exc}")
        return 1
