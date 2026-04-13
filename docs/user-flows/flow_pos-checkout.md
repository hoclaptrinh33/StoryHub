# Flow: POS Checkout

> Actors: Cashier, System
> Preconditions: Cashier đã đăng nhập và có quyền POS; scanner hoạt động.
> Postconditions: Đơn bán ở trạng thái paid hoặc lỗi được phản hồi rõ ràng.

## Tổng quan

Flow bán hàng tối ưu cho quầy: scan nhanh, xác nhận nhanh, tránh popup thừa.

## Happy Path

| Bước | Actor   | Hành động                      | System Response        | API/Event                 | UI State            |
| ---- | ------- | ------------------------------ | ---------------------- | ------------------------- | ------------------- |
| 1    | Cashier | Scan barcode item              | Item tự vào giỏ        | local lookup              | scanning -> success |
| 2    | Cashier | Scan thêm item                 | Cập nhật tổng tạm tính | local state               | success             |
| 3    | Cashier | Chọn discount và split payment | Validate tổng tiền     | local validator           | success             |
| 4    | Cashier | Nhấn F1 hoặc Thanh toán        | Tạo đơn và lock item   | bp_pos-create-order_v1    | paying              |
| 5    | System  | Commit thành công              | Trả order_id, in/toast | event_item-status-changed | success             |

## Sơ đồ luồng

```text
Scan -> Add cart -> Validate payment -> Create order -> Success
             \-> conflict -> Retry banner
```

## Alternative Paths

### Alt 1: Item không sẵn sàng

| Bước | Thay đổi                           | Xử lý                           |
| ---- | ---------------------------------- | ------------------------------- |
| 2    | Item ở trạng thái rented hoặc sold | Báo đỏ ngay, không thêm vào giỏ |

### Alt 2: Tổng split payment lệch

| Bước | Thay đổi                   | Xử lý                               |
| ---- | -------------------------- | ----------------------------------- |
| 3    | Tổng thanh toán không khớp | Khóa nút F1, focus panel thanh toán |

## Edge Cases

| Case                      | Trigger          | System Response     | UI Response      |
| ------------------------- | ---------------- | ------------------- | ---------------- |
| Scan trùng quá nhanh      | cùng barcode lặp | idempotency guard   | chỉ thêm một lần |
| Item bị lock từ quầy khác | concurrent order | ORDER_LOCK_CONFLICT | retry banner     |
| Mất kết nối local backend | service stop     | NETWORK_ERROR       | banner + retry   |

## Error Recovery

| Lỗi                    | Bước xảy ra      | Recovery                                 |
| ---------------------- | ---------------- | ---------------------------------------- |
| ORDER_LOCK_CONFLICT    | tạo đơn          | retry tối đa 3 lần với backoff ngắn      |
| SPLIT_PAYMENT_MISMATCH | validate         | yêu cầu chỉnh payment trước khi tiếp tục |
| NETWORK_ERROR          | mọi bước gọi API | bật chế độ retry manual                  |

## Related Docs

| Doc                                                                            | Vai trò trong flow  |
| ------------------------------------------------------------------------------ | ------------------- |
| [bp_pos-create-order_v1.yaml](../api-reference/v1/bp_pos-create-order_v1.yaml) | API tạo đơn         |
| [ui_pos-main-kiosk.yaml](../ui-contracts/ui_pos-main-kiosk.yaml)               | Giao diện POS chính |
| [lifecycle_item.yaml](../lifecycle/lifecycle_item.yaml)                        | Trạng thái item     |
| [domain_item.yaml](../domain/domain_item.yaml)                                 | Invariants item     |
