# upsertCustomerProfile (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.

> Schema file: [bp_crm-upsert-customer_v1.yaml](./bp_crm-upsert-customer_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: High

## Ý tưởng gốc

CRM cần thao tác nhanh theo số điện thoại, đồng thời quản lý cọc, nợ, membership và blacklist để kiểm soát rủi ro khi thuê.

## Mô tả chức năng (dự kiến)

Tạo mới hoặc cập nhật hồ sơ khách hàng bằng một API duy nhất theo phone. Mọi thay đổi liên quan tài chính phải được kiểm tra và ghi audit log.

## Tham số (dự kiến)

| Tên              | Kiểu    | Bắt buộc | Mô tả                    |
| ---------------- | ------- | -------- | ------------------------ |
| phone            | string  | Có       | Số điện thoại định danh  |
| name             | string  | Có       | Tên khách hàng           |
| membership_level | string  | Có       | standard/silver/gold/vip |
| address          | string  | Không    | Địa chỉ liên hệ          |
| deposit_delta    | number  | Không    | Điều chỉnh cọc           |
| debt_delta       | number  | Không    | Điều chỉnh công nợ       |
| blacklist_flag   | boolean | Không    | Cờ blacklist             |
| request_id       | string  | Có       | Idempotency key          |

## Response Schema (dự kiến)

```json
{
  "customer_id": "CUS-0010",
  "phone": "0901234567",
  "name": "Nguyễn Minh Anh",
  "membership_level": "gold",
  "deposit_balance": 500000,
  "debt": 0,
  "blacklist_flag": false,
  "updated_at": "2026-04-13T23:08:30+07:00"
}
```

## Edge Cases (dự kiến)

| Case                                  | Input                     | Kết quả dự kiến                      |
| ------------------------------------- | ------------------------- | ------------------------------------ |
| Phone sai định dạng                   | phone thiếu chuẩn         | INVALID_PHONE                        |
| Cập nhật làm số dư sai quy tắc        | deposit_delta quá lớn âm  | NEGATIVE_BALANCE_NOT_ALLOWED         |
| Tài khoản blacklist bị sửa trái quyền | cashier mở khóa blacklist | BLACKLISTED_CUSTOMER_MUTATION_DENIED |

## Giả định (Assumptions)

- [ ] Phone là định danh chính ở quầy.
- [ ] Trường tài chính chỉ cập nhật qua transaction.
- [ ] Trạng thái blacklist ảnh hưởng trực tiếp tới quyền thuê.

## Câu hỏi mở (Open Questions)

- [ ] Có cần tách API riêng cho tài chính để tăng bảo mật không?
- [ ] Có cần xác thực OTP khi cập nhật dữ liệu nhạy cảm?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] Upsert theo phone tạo mới/cập nhật đúng.
- [ ] Validation chặn dữ liệu tài chính không hợp lệ.
- [ ] Audit log có đủ before/after, actor, timestamp.

## Gợi ý khi implement

- Tech stack gợi ý: Pydantic schema + SQL transaction + unique index cho phone.
- Lưu ý bảo mật dự kiến: phân quyền theo vai trò, đặc biệt với blacklist.
- Lưu ý hiệu năng dự kiến: cache đọc customer theo phone để tối ưu tìm nhanh ở POS.
