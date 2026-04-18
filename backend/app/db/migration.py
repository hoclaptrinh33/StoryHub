from __future__ import annotations

import argparse
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from app.core.config import get_settings

MIGRATION_VERSION = "0001_initial_schema"
_SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


@dataclass(frozen=True)
class MigrationScript:
    version: str
    up_path: Path
    down_path: Path


def get_migration_script(version: str = MIGRATION_VERSION) -> MigrationScript:
    migration_dir = Path(__file__).resolve().parent / "migrations"
    up_path = migration_dir / f"{version}.up.sql"
    down_path = migration_dir / f"{version}.down.sql"

    if not up_path.exists() or not down_path.exists():
        raise FileNotFoundError(f"Migration files for '{version}' were not found.")

    return MigrationScript(version=version, up_path=up_path, down_path=down_path)


def resolve_database_url(database_url: str | None = None) -> str:
    if database_url:
        return database_url
    return get_settings().database_url


def resolve_sqlite_path(database_url: str) -> Path:
    prefixes = ("sqlite+aiosqlite:///", "sqlite:///")
    for prefix in prefixes:
        if database_url.startswith(prefix):
            raw_path = unquote(database_url[len(prefix) :])
            if raw_path == ":memory:":
                return Path(":memory:")

            db_path = Path(raw_path)
            if not db_path.is_absolute():
                db_path = Path.cwd() / db_path
            return db_path.resolve()

    raise ValueError("Only SQLite database URLs are supported by the migration runner.")


def open_sqlite_connection(database_url: str) -> sqlite3.Connection:
    db_path = resolve_sqlite_path(database_url)

    if str(db_path) != ":memory:":
        db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    cursor = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?;",
        (table_name,),
    )
    return cursor.fetchone() is not None


def _ensure_migrations_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {_SCHEMA_MIGRATIONS_TABLE} (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


def _is_migration_applied(connection: sqlite3.Connection, version: str) -> bool:
    if not _table_exists(connection, _SCHEMA_MIGRATIONS_TABLE):
        return False

    cursor = connection.execute(
        f"SELECT 1 FROM {_SCHEMA_MIGRATIONS_TABLE} WHERE version = ?;",
        (version,),
    )
    return cursor.fetchone() is not None


def apply_schema_migration(
    database_url: str | None = None,
    version: str = MIGRATION_VERSION,
) -> bool:
    resolved_url = resolve_database_url(database_url)
    script = get_migration_script(version)
    connection = open_sqlite_connection(resolved_url)

    try:
        _ensure_migrations_table(connection)
        if _is_migration_applied(connection, version):
            return False

        with connection:
            connection.executescript(script.up_path.read_text(encoding="utf-8"))
            connection.execute(
                f"INSERT INTO {_SCHEMA_MIGRATIONS_TABLE} (version) VALUES (?);",
                (version,),
            )
        return True
    finally:
        connection.close()


def rollback_schema_migration(
    database_url: str | None = None,
    version: str = MIGRATION_VERSION,
) -> bool:
    resolved_url = resolve_database_url(database_url)
    script = get_migration_script(version)
    connection = open_sqlite_connection(resolved_url)

    try:
        _ensure_migrations_table(connection)
        if not _is_migration_applied(connection, version):
            return False

        with connection:
            connection.executescript(script.down_path.read_text(encoding="utf-8"))
            connection.execute(
                f"DELETE FROM {_SCHEMA_MIGRATIONS_TABLE} WHERE version = ?;",
                (version,),
            )
        return True
    finally:
        connection.close()


def get_migration_status(
    database_url: str | None = None,
    version: str = MIGRATION_VERSION,
) -> dict[str, str]:
    resolved_url = resolve_database_url(database_url)
    db_path = resolve_sqlite_path(resolved_url)

    if str(db_path) != ":memory:" and not db_path.exists():
        return {
            "database": str(db_path),
            "migration": version,
            "applied": "no",
            "database_exists": "no",
        }

    connection = open_sqlite_connection(resolved_url)
    try:
        applied = _is_migration_applied(connection, version)
    finally:
        connection.close()

    return {
        "database": str(db_path),
        "migration": version,
        "applied": "yes" if applied else "no",
        "database_exists": "yes",
    }


def run_cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="StoryHub SQLite migration runner")
    parser.add_argument("command", choices=["up", "down", "status"], help="Migration command")
    parser.add_argument(
        "--database-url",
        dest="database_url",
        default=None,
        help="Override STORYHUB_DATABASE_URL.",
    )
    args = parser.parse_args(argv)

    try:
        if args.command == "up":
            changed = apply_schema_migration(database_url=args.database_url)
            print("Migration applied." if changed else "Migration already applied.")
        elif args.command == "down":
            changed = rollback_schema_migration(database_url=args.database_url)
            print("Migration rolled back." if changed else "Migration was not applied.")
        else:
            status = get_migration_status(database_url=args.database_url)
            for key, value in status.items():
                print(f"{key}: {value}")

        return 0
    except Exception as exc:
        print(f"Migration command failed: {exc}")
        return 1
