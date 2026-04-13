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
- thao tác backup/restore

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
