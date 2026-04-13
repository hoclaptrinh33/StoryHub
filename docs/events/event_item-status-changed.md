# Event: item_status_changed

> Schema file: [event_item-status-changed.yaml](./event_item-status-changed.yaml)
> Domain: inventory-rental-pos | Severity: info

## Mô tả

Sự kiện này được phát khi item đổi trạng thái (available, reserved, rented, sold, lost, maintenance), giúp đồng bộ audit và UI vận hành.

## Trigger

- Phát bởi: `bp_inventory-reserve-item_v1`, `bp_pos-create-order_v1`, `bp_rental-create-contract_v1`, `bp_rental-return-items_v1`
- Điều kiện: mutation thành công và trạng thái thay đổi thực tế.

## Payload

| Field      | Kiểu      | Bắt buộc | Mô tả            |
| ---------- | --------- | -------- | ---------------- |
| item_id    | string    | Có       | Mã item          |
| old_status | string    | Có       | Trạng thái trước |
| new_status | string    | Có       | Trạng thái sau   |
| changed_by | string    | Có       | User thao tác    |
| changed_at | date-time | Có       | Thời điểm đổi    |
| source_api | string    | Không    | API nguồn        |

## Consumers

| Consumer                   | Hành động              | Async | Bắt buộc | Khi fail |
| -------------------------- | ---------------------- | ----- | -------- | -------- |
| write_audit_log            | Ghi audit before/after | Không | Có       | retry    |
| refresh_pos_and_rental_ui  | Đồng bộ UI kiosk       | Có    | Không    | skip     |
| update_inventory_analytics | Cập nhật analytics     | Có    | Không    | retry    |

## Luồng xử lý

```text
API mutation -> item_status_changed
  -> write_audit_log
  -> refresh_pos_and_rental_ui
  -> update_inventory_analytics
```

## Lưu ý

- Ordering bật để tránh UI nhận trạng thái sai thứ tự khi thao tác nhanh.
- Consumer phải idempotent vì event có thể bị gửi lặp.
