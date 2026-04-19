-- Migration: Pricing rules + transaction snapshots
-- Version: 0004

ALTER TABLE volume ADD COLUMN p_sell_new INTEGER NOT NULL DEFAULT 30000;

CREATE TABLE IF NOT EXISTS price_rule (
   id                 INTEGER PRIMARY KEY,
   rule_code          TEXT NOT NULL,
   version_no         INTEGER NOT NULL CHECK (version_no > 0),
   status             TEXT NOT NULL CHECK (status IN ('draft', 'active', 'retired')),
   k_rent             REAL NOT NULL CHECK (k_rent > 0),
   k_deposit          REAL NOT NULL CHECK (k_deposit > 0),
   d_floor            INTEGER NOT NULL CHECK (d_floor >= 0),
   used_demand_factor REAL NOT NULL CHECK (used_demand_factor > 0),
   used_cap_ratio     REAL NOT NULL CHECK (used_cap_ratio > 0),
   valid_from         TEXT,
   valid_to           TEXT,
   created_by_user_id TEXT NOT NULL,
   activated_by_user_id TEXT,
   note               TEXT,
   created_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
   updated_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
   activated_at       TEXT,
   UNIQUE(rule_code, version_no)
);

CREATE INDEX IF NOT EXISTS idx_price_rule_status ON price_rule(status);
CREATE INDEX IF NOT EXISTS idx_price_rule_valid_window ON price_rule(valid_from, valid_to);

INSERT INTO price_rule (
   rule_code,
   version_no,
   status,
   k_rent,
   k_deposit,
   d_floor,
   used_demand_factor,
   used_cap_ratio,
   valid_from,
   valid_to,
   created_by_user_id,
   activated_by_user_id,
   note,
   activated_at
)
SELECT
   'default',
   1,
   'active',
   0.2666666667,
   1.0666666667,
   10000,
   1.0,
   1.0,
   CURRENT_TIMESTAMP,
   NULL,
   'system',
   'system',
   'Default pricing rule seeded by migration',
   CURRENT_TIMESTAMP
WHERE NOT EXISTS (
   SELECT 1 FROM price_rule WHERE status = 'active'
);

CREATE TABLE IF NOT EXISTS order_item (
   id                    INTEGER PRIMARY KEY,
   order_type            TEXT NOT NULL CHECK (order_type IN ('sale', 'rental')),
   pos_order_id          INTEGER,
   rental_contract_id    INTEGER,
   pos_order_item_id     INTEGER,
   rental_item_id        INTEGER,
   volume_id             INTEGER NOT NULL,
   item_id               TEXT,
   quantity              INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
   p_sell_new_snapshot   INTEGER NOT NULL CHECK (p_sell_new_snapshot >= 0),
   rent_ratio_snapshot   REAL,
   deposit_ratio_snapshot REAL,
   deposit_floor_snapshot INTEGER,
   final_sell_price      INTEGER,
   final_rent_price      INTEGER,
   final_deposit         INTEGER,
   line_total            INTEGER NOT NULL CHECK (line_total >= 0),
   price_rule_id         INTEGER,
   price_rule_version    INTEGER NOT NULL DEFAULT 0,
   override_applied      INTEGER NOT NULL DEFAULT 0 CHECK (override_applied IN (0, 1)),
   override_reason_code  TEXT,
   override_reason_note  TEXT,
   approved_by_user_id   TEXT,
   approved_via          TEXT CHECK (approved_via IN ('pin', 'card') OR approved_via IS NULL),
   created_at            TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
   FOREIGN KEY (pos_order_id) REFERENCES pos_order(id),
   FOREIGN KEY (rental_contract_id) REFERENCES rental_contract(id),
   FOREIGN KEY (pos_order_item_id) REFERENCES pos_order_item(id),
   FOREIGN KEY (rental_item_id) REFERENCES rental_item(id),
   FOREIGN KEY (volume_id) REFERENCES volume(id),
   FOREIGN KEY (item_id) REFERENCES item(id),
   FOREIGN KEY (price_rule_id) REFERENCES price_rule(id),
   CHECK (
      (order_type = 'sale' AND pos_order_id IS NOT NULL AND rental_contract_id IS NULL)
      OR (order_type = 'rental' AND rental_contract_id IS NOT NULL AND pos_order_id IS NULL)
   )
);

CREATE INDEX IF NOT EXISTS idx_order_item_pos_order_id ON order_item(pos_order_id);
CREATE INDEX IF NOT EXISTS idx_order_item_rental_contract_id ON order_item(rental_contract_id);
CREATE INDEX IF NOT EXISTS idx_order_item_item_id ON order_item(item_id);
CREATE INDEX IF NOT EXISTS idx_order_item_price_rule_version ON order_item(price_rule_version);
