# logic_security-audit-and-locking

## 1) Mục tiêu

Tài liệu này gom 3 lớp bảo vệ quan trọng:

- phân quyền đúng người đúng quyền (RBAC)
- audit đầy đủ để chống gian lận
- khóa transaction để tránh race condition

## 2) RBAC tối thiểu

### cashier

- Được: bán hàng, thuê/trả, xem khách hàng cơ bản
- Không được: sửa giá gốc, xóa lịch sử, backup hệ thống

### manager

- Được: toàn bộ quyền cashier
- Được thêm: hoàn tiền, chỉnh giá, backup thủ công, xem báo cáo tổng hợp
- Override giá tại quầy chỉ hợp lệ khi xác thực manager bằng PIN hoặc thẻ

### owner/admin

- Được: cấu hình hệ thống, phân quyền người dùng, xuất backup/restore

## 3) Audit log bắt buộc

Mọi thao tác mutation phải ghi:

- ai thực hiện (`actor_user_id`)
- làm gì (`action`)
- thực thể nào (`entity_type`, `entity_id`)
- dữ liệu trước/sau (`before_json`, `after_json`)
- thời điểm (`created_at`)

Các hành động bắt buộc audit:

- tạo/sửa/hủy đơn POS
- tạo/gia hạn/kết toán phiếu thuê
- đổi trạng thái item
- đổi giá và rule phạt
- override giá tại POS (ghi rõ giá cũ, giá mới, lý do)
- thao tác backup/restore

## 3.1) Chính sách override giá tại quầy

- Vị trí thao tác: panel thanh toán POS, icon cây bút cạnh tổng tiền
- Chỉ manager được xác thực để mở popup override
- Khi override phải có:
  - `reason_code` bắt buộc từ danh sách chuẩn
  - `reason_note` tùy chọn nếu cần diễn giải chi tiết
- Cashier không có quyền xác nhận override bằng tài khoản của mình
- Mọi override phải ghi `audit_log.action = POS_PRICE_OVERRIDE`
- Dữ liệu audit tối thiểu cho override:
  - `before_json.grand_total`
  - `after_json.grand_total`
  - `after_json.override_reason_code`
  - `after_json.override_actor_user_id`
  - `after_json.order_id`

## 4) Locking strategy

### Item-level lock

- Dùng lock theo `item_id` khi reserve/sell/rent/return
- Lock giữ trong transaction ngắn
- Nếu lock fail -> trả lỗi conflict để client retry

### Contract-level lock

- Dùng khi settle return hoặc extend
- Tránh 2 quầy cùng settle một contract

## 5) Idempotency strategy

Mọi endpoint mutation nhận `request_id`:

- Nếu request_id chưa có: xử lý bình thường và lưu result
- Nếu request_id đã tồn tại: trả lại response cũ, không chạy lại logic

## 6) Validation guardrails

- Không cho số tiền âm
- Không cho hoàn tiền vượt số đã thanh toán
- Không cho due_date mới nhỏ hơn due_date cũ (luồng gia hạn)
- Không cho trả item không thuộc contract

## 7) Backup policy

- Hàng ngày: incremental backup tự động
- Hàng tuần: full backup
- Mỗi backup có checksum và audit log
- Ít nhất 1 bản backup offline ngoài máy quầy
