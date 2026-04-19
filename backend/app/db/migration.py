from __future__ import annotations

import argparse
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from app.core.config import get_settings

MIGRATION_VERSIONS = [
    "0001_initial_schema",
    "0002_add_base_price",
    "0003_create_user_table",
    "0004_pricing_rules_and_snapshots",
]
_SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


@dataclass(frozen=True)
class MigrationScript:
    version: str
    up_path: Path
    down_path: Path


def get_migration_script(version: str) -> MigrationScript:
    # Check both potential migration directories
    # 1. app/db/migrations (custom)
    # 2. migrations/ (root)
    migration_dir = Path(__file__).resolve().parent / "migrations"
    
    up_path = migration_dir / f"{version}.up.sql"
    down_path = migration_dir / f"{version}.down.sql"

    if not up_path.exists():
        # Fallback to root migrations if needed, but standard is the app/db/migrations
        raise FileNotFoundError(f"Migration file '{up_path}' was not found.")

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
    version: str | None = None,
    *,
    return_count: bool = False,
) -> bool | int:
    resolved_url = resolve_database_url(database_url)
    connection = open_sqlite_connection(resolved_url)
    versions_to_apply = [version] if version else MIGRATION_VERSIONS
    applied_count = 0

    try:
        _ensure_migrations_table(connection)
        for v in versions_to_apply:
            if _is_migration_applied(connection, v):
                continue
            
            try:
                script = get_migration_script(v)
            except FileNotFoundError:
                print(f"Warning: Migration script for '{v}' missing locally. Skipping.")
                continue

            with connection:
                connection.executescript(script.up_path.read_text(encoding="utf-8"))
                connection.execute(
                    f"INSERT INTO {_SCHEMA_MIGRATIONS_TABLE} (version) VALUES (?);",
                    (v,),
                )
                print(f"Applied migration: {v}")
                applied_count += 1
        if return_count:
            return applied_count
        return applied_count > 0
    finally:
        connection.close()


def rollback_schema_migration(
    database_url: str | None = None,
    version: str | None = None,
    *,
    return_count: bool = False,
) -> bool | int:
    resolved_url = resolve_database_url(database_url)
    connection = open_sqlite_connection(resolved_url)

    try:
        _ensure_migrations_table(connection)
        if version:
            versions_to_rollback = [version]
        else:
            cursor = connection.execute(
                f"SELECT version FROM {_SCHEMA_MIGRATIONS_TABLE} ORDER BY applied_at DESC, version DESC"
            )
            versions_to_rollback = [str(row["version"]) for row in cursor.fetchall()]

        if not versions_to_rollback:
            if return_count:
                return 0
            return False

        rolled_back = 0
        for migration_version in versions_to_rollback:
            if not _is_migration_applied(connection, migration_version):
                continue

            script = get_migration_script(migration_version)
            with connection:
                connection.executescript(script.down_path.read_text(encoding="utf-8"))
                connection.execute(
                    f"DELETE FROM {_SCHEMA_MIGRATIONS_TABLE} WHERE version = ?;",
                    (migration_version,),
                )
                print(f"Rolled back migration: {migration_version}")
                rolled_back += 1

        if return_count:
            return rolled_back
        return rolled_back > 0
    finally:
        connection.close()


def get_migration_status(
    database_url: str | None = None,
) -> list[dict[str, str]]:
    resolved_url = resolve_database_url(database_url)
    db_path = resolve_sqlite_path(resolved_url)

    if str(db_path) != ":memory:" and not db_path.exists():
        return []

    connection = open_sqlite_connection(resolved_url)
    _ensure_migrations_table(connection)
    
    results = []
    try:
        for v in MIGRATION_VERSIONS:
            applied = _is_migration_applied(connection, v)
            results.append({
                "version": v,
                "applied": "yes" if applied else "no"
            })
    finally:
        connection.close()
    return results


def run_cli(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="StoryHub SQLite migration runner")
    parser.add_argument("command", choices=["up", "down", "status"], help="Migration command")
    parser.add_argument(
        "--version",
        dest="version",
        default=None,
        help="Specific version for up/down command.",
    )
    parser.add_argument(
        "--database-url",
        dest="database_url",
        default=None,
        help="Override STORYHUB_DATABASE_URL.",
    )
    args = parser.parse_args(argv)

    try:
        if args.command == "up":
            applied = apply_schema_migration(
                database_url=args.database_url,
                version=args.version,
                return_count=True,
            )
            if applied > 0:
                print(f"Successfully applied {applied} migration(s).")
            else:
                print("No new migrations to apply.")
        elif args.command == "down":
            rolled = rollback_schema_migration(
                database_url=args.database_url,
                version=args.version,
                return_count=True,
            )
            if rolled > 0:
                print("Rollback successful.")
            else:
                print("No migration found to rollback.")
        else:
            statuses = get_migration_status(database_url=args.database_url)
            print(f"{'Version':<30} | {'Applied':<10}")
            print("-" * 45)
            for s in statuses:
                print(f"{s['version']:<30} | {s['applied']:<10}")

        return 0
    except Exception as exc:
        print(f"Migration command failed: {exc}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_cli())
