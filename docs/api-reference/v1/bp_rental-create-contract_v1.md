# createRentalContract (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.

> Schema file: [bp_rental-create-contract_v1.yaml](./bp_rental-create-contract_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: High

## Ý tưởng gốc

Thuê truyện phải thao tác trên từng item vật lý, cần lock tránh xung đột và lưu snapshot giá thuê/cọc để lịch sử không sai lệch.

## Mô tả chức năng (dự kiến)

API tạo contract thuê mới với `customer_id`, danh sách item và `due_date`. Hệ thống tự tính hoặc nhận cọc, lưu snapshot từng item, cập nhật trạng thái item sang `rented`.

## Tham số (dự kiến)

| Tên            | Kiểu          | Bắt buộc | Mô tả           |
| -------------- | ------------- | -------- | --------------- |
| customer_id    | string        | Có       | Khách thuê      |
| item_ids       | array<string> | Có       | Danh sách item  |
| due_date       | datetime      | Có       | Hạn trả         |
| deposit_policy | string        | Không    | auto/manual     |
| manual_deposit | number        | Không    | Cọc nhập tay    |
| request_id     | string        | Có       | Idempotency key |

## Response Schema (dự kiến)

```json
{
  "contract_id": "RCT-0001",
  "customer_id": "CUS-0008",
  "rent_date": "2026-04-13T23:08:30+07:00",
  "due_date": "2026-04-20T23:59:59+07:00",
  "deposit_total": 300000,
  "rental_items": [
    {
      "item_id": "ITM-0003",
      "final_rent_price": 15000,
      "final_deposit": 100000
    },
    {
      "item_id": "ITM-0004",
      "final_rent_price": 15000,
      "final_deposit": 200000
    }
  ]
}
```

## Edge Cases (dự kiến)

| Case                | Input                        | Kết quả dự kiến      |
| ------------------- | ---------------------------- | -------------------- |
| Khách blacklist     | customer_id bị cấm thuê      | CUSTOMER_BLACKLISTED |
| Item không sẵn sàng | item đã sold/rented          | ITEM_NOT_AVAILABLE   |
| Cọc thiếu           | manual_deposit thấp hơn rule | DEPOSIT_NOT_ENOUGH   |
| Lock item lỗi       | nhiều quầy thao tác cùng lúc | RENTAL_LOCK_CONFLICT |

## Giả định (Assumptions)

- [ ] Mọi contract mới đều có idempotency key.
- [ ] Snapshot giá thuê/cọc là bắt buộc cho từng rental item.
- [ ] Khách blacklist không thể tạo hợp đồng mới.

## Câu hỏi mở (Open Questions)

- [ ] Có cần cho phép waive cọc cho VIP không?
- [ ] Có cần cảnh báo khi khách còn debt vượt ngưỡng?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] Contract tạo xong, item phải ở trạng thái `rented`.
- [ ] Snapshot giá/cọc có đủ trên mọi line item.
- [ ] Nếu request_id trùng thì trả cùng kết quả cũ.

## Gợi ý khi implement

- Tech stack gợi ý: lock theo item + commit atomically.
- Lưu ý bảo mật dự kiến: phân quyền theo vai trò và chi nhánh.
- Lưu ý hiệu năng dự kiến: batch query item để giảm round-trip DB.
