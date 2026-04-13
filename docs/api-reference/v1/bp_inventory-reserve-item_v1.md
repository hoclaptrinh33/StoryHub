# reserveInventoryItem (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.
> Khi backend implement xong, chạy lại skill ở mode detailed để đồng bộ.

> Schema file: [bp_inventory-reserve-item_v1.yaml](./bp_inventory-reserve-item_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: High

## Ý tưởng gốc

Giữ chỗ item cho khách để tránh bị người khác thuê hoặc mua trước, đồng thời phải có cơ chế auto release khi quá hạn.

## Mô tả chức năng (dự kiến)

Tạo reservation trên một item cụ thể với thời gian hiệu lực rõ ràng. API cần hỗ trợ idempotency và lock item để tránh race condition.

## Tham số (dự kiến)

| Tên                 | Kiểu    | Bắt buộc | Mô tả                 |
| ------------------- | ------- | -------- | --------------------- |
| item_id             | string  | Có       | Mã item vật lý        |
| customer_id         | string  | Có       | Mã khách hàng giữ chỗ |
| reservation_minutes | integer | Có       | Số phút giữ chỗ       |
| request_id          | string  | Có       | Idempotency key       |

## Response Schema (dự kiến)

```json
{
  "reservation_id": "resv_001",
  "item_id": "ITM-0001",
  "customer_id": "CUS-0008",
  "status": "active",
  "reserved_at": "2026-04-13T23:08:30+07:00",
  "reservation_expire_at": "2026-04-13T23:38:30+07:00"
}
```

## Edge Cases (dự kiến)

| Case                          | Input                 | Kết quả dự kiến            |
| ----------------------------- | --------------------- | -------------------------- |
| Item đang rented              | item_id hợp lệ        | ITEM_NOT_AVAILABLE         |
| Item đã có reservation active | item_id hợp lệ        | ITEM_ALREADY_RESERVED      |
| reservation_minutes = 0       | giá trị không hợp lệ  | INVALID_RESERVATION_WINDOW |
| Lock item thất bại            | concurrent access cao | RESERVATION_LOCK_TIMEOUT   |

## Giả định (Assumptions)

- [ ] Mỗi item chỉ có một reservation active tại một thời điểm.
- [ ] Reservation hết hạn tự động bằng kiểm tra realtime khi query.
- [ ] Cron cleanup chỉ là cơ chế dọn dẹp bổ sung.

## Câu hỏi mở (Open Questions)

- [ ] Có cần API convert reservation sang bán hoặc thuê hay xử lý trong API khác?
- [ ] Có cần thông báo realtime khi reservation sắp hết hạn?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] Tạo reservation thành công trả đủ `reserved_at` và `reservation_expire_at`.
- [ ] Item không thể bị reserve đồng thời bởi hai request khác nhau.
- [ ] request_id trùng phải trả response cũ, không tạo mới.

## Gợi ý khi implement

- Tech stack gợi ý: FastAPI + SQLAlchemy transaction + item-level lock.
- Lưu ý bảo mật dự kiến: chỉ `cashier` và `manager` mới được gọi API.
- Lưu ý hiệu năng dự kiến: reservation lookup nên có index theo `item_id` và `expire_at`.
