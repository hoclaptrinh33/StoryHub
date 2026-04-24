-- Migration 0006: Rental emergency refund tracking tables

CREATE TABLE IF NOT EXISTS rental_refund (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id        INTEGER NOT NULL,
    reason             TEXT NOT NULL,
    refund_method      TEXT NOT NULL CHECK(refund_method IN ('cash', 'bank_transfer', 'e_wallet', 'original_method')),
    refunded_total     INTEGER NOT NULL CHECK(refunded_total >= 0),
    request_id         TEXT NOT NULL UNIQUE,
    created_by_user_id TEXT NOT NULL,
    created_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(contract_id) REFERENCES rental_contract(id)
);

CREATE INDEX IF NOT EXISTS idx_rental_refund_contract_id
ON rental_refund(contract_id);

CREATE TABLE IF NOT EXISTS rental_refund_item (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    refund_id      INTEGER NOT NULL,
    rental_item_id INTEGER NOT NULL,
    item_id        TEXT NOT NULL,
    amount         INTEGER NOT NULL CHECK(amount >= 0),
    FOREIGN KEY(refund_id) REFERENCES rental_refund(id),
    FOREIGN KEY(rental_item_id) REFERENCES rental_item(id),
    UNIQUE(refund_id, rental_item_id)
);

