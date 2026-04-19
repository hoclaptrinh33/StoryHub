# createPosOrder (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.

> Schema file: [bp_pos-create-order_v1.yaml](./bp_pos-create-order_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: High

## Ý tưởng gốc

Luồng bán hàng phải cực nhanh: scan item, áp dụng discount, thanh toán (kể cả split payment), hoàn tất với số bước tối thiểu.

## Mô tả chức năng (dự kiến)

API tạo đơn bán cuối cùng, khóa item để tránh bán trùng, lưu snapshot giá và cập nhật trạng thái item sang `sold` sau khi thanh toán thành công.

## Tham số (dự kiến)

| Tên               | Kiểu          | Bắt buộc | Mô tả                                                         |
| ----------------- | ------------- | -------- | ------------------------------------------------------------- |
| customer_id       | string        | Không    | Mã khách (khách lẻ có thể bỏ qua)                             |
| item_ids          | array<string> | Có       | Danh sách item cần bán                                        |
| discount_type     | string        | Có       | none/percent/amount                                           |
| discount_value    | number        | Có       | Giá trị giảm                                                  |
| split_payments    | array<object> | Có       | Danh sách phương thức thanh toán                              |
| checkout_override | object        | Không    | Override giá tại quầy, cần manager xác thực và lý do bắt buộc |
| note              | string        | Không    | Ghi chú                                                       |
| request_id        | string        | Có       | Idempotency key                                               |

`checkout_override` gồm:

- `new_grand_total`: tổng tiền mới sau override
- `reason_code`: mã lý do bắt buộc (ví dụ: `vip_customer`, `complaint_recovery`, `extra_damage`)
- `reason_note`: ghi chú chi tiết (tuỳ chọn)
- `manager_approval_token`: token sinh sau khi manager quét thẻ hoặc nhập PIN thành công

## Response Schema (dự kiến)

```json
{
  "order_id": "ORD-20260413-0001",
  "status": "paid",
  "subtotal": 180000,
  "discount_total": 10000,
  "grand_total": 170000,
  "price_rule_version": 12,
  "price_override_applied": true,
  "override_reason_code": "complaint_recovery",
  "payment_breakdown": [
    { "method": "cash", "amount": 100000 },
    { "method": "bank_transfer", "amount": 70000 }
  ],
  "line_items": [
    { "item_id": "ITM-0001", "final_sell_price": 90000 },
    { "item_id": "ITM-0002", "final_sell_price": 90000 }
  ]
}
```

## Edge Cases (dự kiến)

| Case                           | Input                                               | Kết quả dự kiến           |
| ------------------------------ | --------------------------------------------------- | ------------------------- |
| Item đã rented                 | item_ids chứa item không available                  | ITEM_NOT_AVAILABLE        |
| Split payment lệch tổng        | tổng payment != grand_total                         | SPLIT_PAYMENT_MISMATCH    |
| Lỗi snapshot giá               | không lấy được giá cuối                             | PRICE_SNAPSHOT_MISSING    |
| Lock xung đột                  | 2 quầy bán cùng item                                | ORDER_LOCK_CONFLICT       |
| Override chưa xác thực manager | có `checkout_override` nhưng thiếu token hợp lệ     | MANAGER_APPROVAL_REQUIRED |
| Override thiếu lý do           | có `checkout_override` nhưng không có `reason_code` | OVERRIDE_REASON_REQUIRED  |
| Override quá biên độ           | `new_grand_total` thấp hơn policy cho phép          | OVERRIDE_BELOW_FLOOR      |

## Giả định (Assumptions)

- [ ] Item bán xong không quay lại kho available.
- [ ] Snapshot giá lưu cứng ở `order_item` và phản chiếu ở `pos_order_item`.
- [ ] request_id trùng sẽ trả kết quả đã tạo trước đó.

## Câu hỏi mở (Open Questions)

- [ ] Có cần API sửa đơn sau thanh toán hay làm bằng luồng hủy + tạo lại?
- [ ] Có cần hạn mức giảm giá theo vai trò người dùng?
- [ ] Có cần bắt buộc nhập ghi chú tự do cho một số `reason_code` nhạy cảm?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] Đơn bán tạo thành công luôn có snapshot giá từng item.
- [ ] Không có trường hợp một item bị bán hai lần đồng thời.
- [ ] Split payment được validate tuyệt đối trước khi commit.
- [ ] Nếu có override thì luôn có manager approval hợp lệ và audit log đầy đủ.

## Gợi ý khi implement

- Tech stack gợi ý: transaction + item lock + idempotency table.
- Lưu ý bảo mật dự kiến: cashier và manager đều có thể tạo đơn; hoàn tiền tách quyền cao hơn.
- Lưu ý bảo mật dự kiến: override giá tại quầy phải có manager token + reason_code và log action `POS_PRICE_OVERRIDE`.
- Lưu ý hiệu năng dự kiến: xử lý lock theo batch item để giảm thời gian giữ transaction.
