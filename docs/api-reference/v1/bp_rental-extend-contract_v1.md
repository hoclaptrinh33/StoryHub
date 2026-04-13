# extendRentalContract (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.

> Schema file: [bp_rental-extend-contract_v1.yaml](./bp_rental-extend-contract_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: High

## Ý tưởng gốc

Luồng cho thuê cần hỗ trợ gia hạn hợp đồng, tránh thao tác thủ công và giữ chính xác trạng thái cọc/nợ.

## Mô tả chức năng (dự kiến)

API gia hạn due_date cho contract đang active hoặc overdue, có thể yêu cầu thêm cọc và ghi đầy đủ audit log.

## Tham số (dự kiến)

| Tên                | Kiểu     | Bắt buộc | Mô tả                |
| ------------------ | -------- | -------- | -------------------- |
| contract_id        | string   | Có       | Hợp đồng cần gia hạn |
| new_due_date       | datetime | Có       | Hạn trả mới          |
| extension_reason   | string   | Không    | Lý do gia hạn        |
| additional_deposit | number   | Không    | Cọc bổ sung          |
| request_id         | string   | Có       | Idempotency key      |

## Response Schema (dự kiến)

```json
{
  "contract_id": "RCT-0001",
  "old_due_date": "2026-04-20T23:59:59+07:00",
  "new_due_date": "2026-04-25T23:59:59+07:00",
  "additional_fee": 15000,
  "additional_deposit": 50000,
  "status": "active"
}
```

## Edge Cases (dự kiến)

| Case                       | Input                        | Kết quả dự kiến         |
| -------------------------- | ---------------------------- | ----------------------- |
| Contract không tồn tại     | contract_id sai              | CONTRACT_NOT_FOUND      |
| Contract đã closed         | contract đã tất toán         | CONTRACT_ALREADY_CLOSED |
| Due date mới sai           | new_due_date <= old_due_date | INVALID_DUE_DATE        |
| Không đủ điều kiện gia hạn | policy chặn                  | EXTENSION_NOT_ALLOWED   |

## Giả định (Assumptions)

- [ ] Hợp đồng có thể gia hạn nhiều lần trước khi đóng.
- [ ] Gia hạn có thể tạo thêm phí và cọc.
- [ ] Mọi thay đổi phải lưu lịch sử để báo cáo và audit.

## Câu hỏi mở (Open Questions)

- [ ] Có cần cho phép manager override policy gia hạn không?
- [ ] Có cần gửi thông báo khách hàng khi hợp đồng được gia hạn?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] due_date được cập nhật đúng theo yêu cầu hợp lệ.
- [ ] Cọc hoặc phí bổ sung được tính đúng theo policy.
- [ ] request_id trùng không tạo thay đổi lặp.

## Gợi ý khi implement

- Tech stack gợi ý: policy check trước update, lock contract theo transaction.
- Lưu ý bảo mật dự kiến: giới hạn quyền theo role.
- Lưu ý hiệu năng dự kiến: index `contract_id` + `due_date` cho truy vấn overdue nhanh.
