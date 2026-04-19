-- Migration rollback: Pricing rules + transaction snapshots
-- Version: 0004

drop index if exists idx_order_item_price_rule_version;
drop index if exists idx_order_item_item_id;
drop index if exists idx_order_item_rental_contract_id;
drop index if exists idx_order_item_pos_order_id;
drop table if exists order_item;

drop index if exists idx_price_rule_valid_window;
drop index if exists idx_price_rule_status;
drop table if exists price_rule;

-- SQLite does not support DROP COLUMN safely for this project migration flow.
-- Column volume.p_sell_new is intentionally kept on rollback of version 0004.