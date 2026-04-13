# refundPosOrder (Blueprint)

> ⚠️ BLUEPRINT — Tài liệu sinh từ yêu cầu nghiệp vụ, chưa có code thực tế.

> Schema file: [bp_pos-refund-order_v1.yaml](./bp_pos-refund-order_v1.yaml)
> Version: 0.1.0-blueprint | Status: Blueprint | Confidence: High

## Ý tưởng gốc

POS bắt buộc có khả năng hoàn tiền và sửa sai giao dịch, nhưng cần kiểm soát chặt để tránh thất thoát.

## Mô tả chức năng (dự kiến)

Hoàn tiền cho đơn bán theo danh sách item hoặc theo toàn đơn. API phải validate chính sách hoàn tiền, snapshot số tiền hoàn và ghi audit đầy đủ.

## Tham số (dự kiến)

| Tên           | Kiểu          | Bắt buộc | Mô tả               |
| ------------- | ------------- | -------- | ------------------- |
| order_id      | string        | Có       | Đơn cần hoàn tiền   |
| refund_items  | array<object> | Có       | Danh sách item hoàn |
| reason        | string        | Có       | Lý do hoàn tiền     |
| refund_method | string        | Không    | Phương thức hoàn    |
| request_id    | string        | Có       | Idempotency key     |

## Response Schema (dự kiến)

```json
{
  "refund_id": "RFD-0001",
  "order_id": "ORD-20260413-0001",
  "refunded_total": 90000,
  "order_status": "partially_refunded",
  "processed_at": "2026-04-13T23:08:30+07:00"
}
```

## Edge Cases (dự kiến)

| Case                     | Input              | Kết quả dự kiến            |
| ------------------------ | ------------------ | -------------------------- |
| Đơn không tồn tại        | order_id sai       | ORDER_NOT_FOUND            |
| Quá hạn hoàn tiền        | order quá cũ       | REFUND_WINDOW_EXPIRED      |
| Item đã hoàn trước đó    | refund_items trùng | ITEM_ALREADY_REFUNDED      |
| Tổng hoàn vượt số đã trả | dữ liệu hoàn sai   | REFUND_EXCEEDS_PAID_AMOUNT |

## Giả định (Assumptions)

- [ ] Refund chỉ cho phép manager thực hiện.
- [ ] Trạng thái đơn chuyển `partially_refunded` hoặc `refunded`.
- [ ] Refund luôn tạo record mới, không sửa lịch sử thanh toán cũ.

## Câu hỏi mở (Open Questions)

- [ ] Có cần giới hạn số lần refund trên mỗi order không?
- [ ] Có cần luồng duyệt refund cho nhân viên mới?

## Tiêu chí nghiệm thu (Acceptance Criteria)

- [ ] Không có trường hợp hoàn vượt số đã thanh toán.
- [ ] request_id trùng không tạo refund record trùng.
- [ ] Mọi refund đều truy vết được actor và lý do.

## Gợi ý khi implement

- Tech stack gợi ý: immutable refund ledger + transaction.
- Lưu ý bảo mật dự kiến: role manager bắt buộc.
- Lưu ý hiệu năng dự kiến: index theo `order_id` và `processed_at` cho truy vấn báo cáo.
