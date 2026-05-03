from __future__ import annotations

from sqlalchemy import text

from app.db.session import engine

_RUNTIME_TABLE_DDL = (
    """
    CREATE TABLE IF NOT EXISTS idempotency_record (
        id INTEGER PRIMARY KEY,
        scope TEXT NOT NULL,
        request_id TEXT NOT NULL,
        status_code INTEGER NOT NULL,
        response_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(scope, request_id)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_idempotency_scope_created_at
    ON idempotency_record(scope, created_at DESC);
    """,
    """
    CREATE TABLE IF NOT EXISTS pos_refund (
        id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        refund_method TEXT NOT NULL,
        refunded_total INTEGER NOT NULL CHECK (refunded_total >= 0),
        request_id TEXT NOT NULL UNIQUE,
        created_by_user_id TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(order_id) REFERENCES pos_order(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS pos_refund_item (
        id INTEGER PRIMARY KEY,
        refund_id INTEGER NOT NULL,
        order_item_id INTEGER NOT NULL,
        volume_id INTEGER NOT NULL,
        amount INTEGER NOT NULL CHECK (amount >= 0),
        FOREIGN KEY(refund_id) REFERENCES pos_refund(id),
        FOREIGN KEY(order_item_id) REFERENCES pos_order_item(id),
        UNIQUE(refund_id, order_item_id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS inventory_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id TEXT NOT NULL,
        title_name TEXT,
        sub_text TEXT,
        change_qty INTEGER DEFAULT 0,
        old_qty INTEGER,
        new_qty INTEGER,
        note TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    """,
)


async def ensure_runtime_tables() -> None:
    async with engine.begin() as connection:
        for statement in _RUNTIME_TABLE_DDL:
            await connection.execute(text(statement))
            
        # Ensure 'type' column exists in 'item' table (SQLite only)
        # This is a safe migration for SQLite that won't fail if the column already exists.
        try:
            # PRAGMA is not easily used with AsyncSession execute for checking,
            # so we use a safe ALTER TABLE within a try-except block.
            await connection.execute(text("ALTER TABLE item ADD COLUMN type TEXT DEFAULT 'retail'"))
            print("Successfully added 'type' column to 'item' table.")
        except Exception:
            # SQLite throws error if column already exists
            pass

