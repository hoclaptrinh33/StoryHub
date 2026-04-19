# schema_storyhub-core

## 1) Mục tiêu schema

Schema ưu tiên:

- Theo dõi từng bản sao vật lý (`item`) theo vòng đời thuê/bán
- Lưu snapshot giá tại thời điểm giao dịch
- Chống gian lận bằng audit log đầy đủ before/after
- Hỗ trợ offline-first với transaction rõ ràng và phục hồi từ backup

## 2) Bảng lõi nghiệp vụ

### title

- `id` (PK)
- `name`
- `author`
- `publisher`
- `genre`
- `description`
- `cover_url`
- `created_at`, `updated_at`, `deleted_at`

### volume

- `id` (PK)
- `title_id` (FK -> title.id)
- `volume_number`
- `isbn` (nullable)
- `p_sell_new` (Giá niêm yết bán mới, là giá gốc duy nhất của volume)
- `retail_stock` (Số lượng tồn kho bán lẻ trực tiếp - default 0)
- `created_at`, `updated_at`, `deleted_at`

Ràng buộc:

- unique (`title_id`, `volume_number`)

### price_rule

- `id` (PK)
- `rule_code` (unique, ví dụ `k_rent_default`, `k_deposit_default`, `used_cap`)
- `rule_group` (`rent|deposit|used_sale|override_policy`)
- `scope_type` (`global|genre|title|volume|condition_level`)
- `scope_ref_id` (nullable, id theo scope_type)
- `value`
- `value_type` (`ratio|amount|percent`)
- `status` (`draft|active|archived`)
- `valid_from`
- `valid_to` (nullable)
- `version_no`
- `created_by_user_id`
- `approved_by_user_id` (nullable)
- `approved_at` (nullable)
- `note`
- `created_at`, `updated_at`, `deleted_at`

Index đề xuất:

- `idx_price_rule_group_status`
- `idx_price_rule_scope`
- `idx_price_rule_valid_window`

### item

- `id` (PK, SKU/barcode)
- `volume_id` (FK -> volume.id)
- `condition_level` (100, 80, ...)
- `status` (`available|reserved|rented|lost|maintenance` - Bỏ trạng thái `sold`, bảng này chỉ dành riêng lưu Physical Rental Item)
- `health_percent`
- `notes`
- `reserved_by_customer_id` (nullable)
- `reserved_at` (nullable)
- `reservation_expire_at` (nullable)
- `version_no` (optimistic locking)
- `created_at`, `updated_at`, `deleted_at`

Index đề xuất:

- `idx_item_status`
- `idx_item_reservation_expire`
- `idx_item_volume_id`

### customer

- `id` (PK)
- `name`
- `phone` (unique)
- `address`
- `membership_level`
- `deposit_balance`
- `debt`
- `blacklist_flag`
- `created_at`, `updated_at`, `deleted_at`

### reservation

- `id` (PK)
- `item_id` (FK -> item.id)
- `customer_id` (FK -> customer.id)
- `status` (`active|expired|converted|cancelled`)
- `reserved_at`
- `expire_at`
- `converted_to` (`sold|rented`, nullable)
- `created_by_user_id`

### pos_order

- `id` (PK)
- `customer_id` (nullable)
- `status` (`draft|paid|cancelled|refunded|partially_refunded`)
- `subtotal`
- `discount_type` (`percent|amount|none`)
- `discount_value`
- `discount_total`
- `grand_total`
- `paid_total`
- `request_id` (idempotency key)
- `created_by_user_id`
- `created_at`, `updated_at`, `deleted_at`

### order_item

- `id` (PK)
- `source_type` (`pos_sale|rental_contract|used_sale`)
- `source_id` (order_id hoặc contract_id)
- `item_id` (FK -> item.id)
- `volume_id` (FK -> volume.id)
- `price_rule_version` (version rule dùng để tính tại thời điểm giao dịch)
- `p_sell_new_snapshot`
- `final_sell_price` (nullable)
- `final_rent_price` (nullable)
- `final_deposit` (nullable)
- `used_sale_price` (nullable)
- `price_override_flag` (default false)
- `override_reason_code` (nullable)
- `override_note` (nullable)
- `override_actor_user_id` (nullable)
- `override_approved_by_user_id` (nullable)
- `created_at`

Ghi chú:

- Đây là lớp snapshot giá chuẩn cho mọi giao dịch bán, thuê, cọc, bán truyện cũ.
- Snapshot phải lưu cứng theo thời điểm tạo giao dịch để báo cáo lịch sử không lệch khi rule đổi.

Index đề xuất:

- `idx_order_item_source`
- `idx_order_item_item_id`
- `idx_order_item_rule_version`
- `idx_order_item_override_flag`

### pos_order_item

- `id` (PK)
- `order_id` (FK -> pos_order.id)
- `order_item_id` (FK -> order_item.id)
- `item_id` (FK -> item.id)
- `final_sell_price` (mirror từ order_item.final_sell_price)
- `quantity` (default 1)
- `line_total`

### pos_payment

- `id` (PK)
- `order_id` (FK -> pos_order.id)
- `method` (`cash|bank_transfer|e_wallet|card`)
- `amount`
- `paid_at`

### rental_contract

- `id` (PK)
- `customer_id` (FK -> customer.id)
- `status` (`active|partial_returned|closed|overdue|cancelled`)
- `rent_date`
- `due_date`
- `deposit_total`
- `remaining_deposit`
- `debt_total`
- `request_id` (idempotency key)
- `created_by_user_id`
- `created_at`, `updated_at`, `deleted_at`

### rental_item

- `id` (PK)
- `contract_id` (FK -> rental_contract.id)
- `order_item_id` (FK -> order_item.id)
- `item_id` (FK -> item.id)
- `final_rent_price` (mirror từ order_item.final_rent_price)
- `final_deposit` (mirror từ order_item.final_deposit)
- `status` (`rented|returned|lost`)
- `condition_before`
- `condition_after` (nullable)

### rental_settlement

- `id` (PK)
- `contract_id` (FK -> rental_contract.id)
- `rental_fee`
- `late_fee`
- `damage_fee`
- `lost_fee`
- `total_fee`
- `deducted_from_deposit`
- `refund_to_customer`
- `remaining_debt`
- `settled_at`

### metadata_cache

- `id` (PK)
- `query_key` (unique)
- `source`
- `payload_json`
- `confidence`
- `cached_at`
- `expire_at`

### backup_job

- `id` (PK)
- `backup_type` (`full|incremental`)
- `status` (`queued|running|success|failed`)
- `file_path`
- `checksum`
- `error_message` (nullable)
- `started_at`, `finished_at`
- `created_by_user_id`

### audit_log

- `id` (PK)
- `actor_user_id`
- `action`
- `entity_type`
- `entity_id`
- `before_json`
- `after_json`
- `ip_address`
- `device_id`
- `created_at`

## 3) Quy tắc dữ liệu quan trọng

- Không hard delete dữ liệu nghiệp vụ, dùng `deleted_at`
- Mọi mutation liên quan tiền phải chạy trong transaction
- Mọi thao tác đổi trạng thái item phải ghi audit log
- Reservation expiry cần kiểm tra real-time mỗi lần query item
- Cron cleanup chỉ là lớp dọn dẹp phụ trợ
- `volume` chỉ giữ giá gốc `p_sell_new`, không lưu cứng rent/deposit/used price tại đây
- Rent, deposit, used sale phải tính từ `price_rule` đang active và lưu snapshot vào `order_item`
- Thay đổi rule chỉ áp dụng giao dịch mới, không hồi tố snapshot đã chốt
- Nếu có override giá tại quầy, bắt buộc lưu `override_reason_code` và actor phê duyệt

## 4) Gợi ý migration về sau

- Bổ sung SQLCipher khi phát hành production desktop
- Tách bảng ảnh kiểm định (`item_inspection_media`) cho before/after return
- Khi cần sync cloud: thêm `sync_state`, `sync_version`, `last_synced_at`
