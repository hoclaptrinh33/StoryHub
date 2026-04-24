-- ============================================================
-- Migration 0005: Admin redesign - Tạo 3 bảng mới cho admin
-- Không thay đổi bảng hiện có
-- ============================================================

-- Bảng Voucher (mã giảm giá)
CREATE TABLE IF NOT EXISTS voucher (
    id            INTEGER  PRIMARY KEY AUTOINCREMENT,
    code          TEXT     UNIQUE NOT NULL,
    voucher_type  TEXT     NOT NULL CHECK(voucher_type IN ('percent', 'amount')),
    value         INTEGER  NOT NULL CHECK(value > 0),
    min_spend     INTEGER  NOT NULL DEFAULT 0,
    max_discount  INTEGER  NULL,
    max_uses      INTEGER  NULL,
    current_uses  INTEGER  NOT NULL DEFAULT 0,
    start_at      TEXT     NULL,
    end_at        TEXT     NULL,
    is_active     INTEGER  NOT NULL DEFAULT 1,
    created_at    TEXT     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TEXT     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Chương trình khuyến mãi tự động (theo ngày trong tuần)
CREATE TABLE IF NOT EXISTS automatic_promotion (
    id               INTEGER  PRIMARY KEY AUTOINCREMENT,
    name             TEXT     NOT NULL,
    day_of_week      INTEGER  NOT NULL CHECK(day_of_week BETWEEN 0 AND 6), -- 0=Mon, 6=Sun
    discount_percent INTEGER  NOT NULL CHECK(discount_percent BETWEEN 1 AND 100),
    is_active        INTEGER  NOT NULL DEFAULT 1,
    created_at       TEXT     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TEXT     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Bảng Cấu hình hệ thống (key-value)
CREATE TABLE IF NOT EXISTS system_config (
    config_key   TEXT  PRIMARY KEY NOT NULL,
    config_value TEXT  NOT NULL,
    description  TEXT  NULL,
    updated_at   TEXT  NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Dữ liệu mặc định cho cấu hình cửa hàng
INSERT OR IGNORE INTO system_config (config_key, config_value, description) VALUES
    ('shop_name',       'StoryHub Pro',                        'Tên cửa hàng (in trên hóa đơn)'),
    ('shop_address',    '123 Đường ABC, Quận XYZ, TP.HCM',    'Địa chỉ cửa hàng'),
    ('shop_phone',      '0123 456 789',                        'Số điện thoại liên hệ'),
    ('bill_footer',     'Cảm ơn quý khách! Hẹn gặp lại.',     'Lời chào cuối hóa đơn'),
    ('penalty_per_day', '2000',                                 'Phí phạt quá hạn (đồng/ngày/cuốn)');
