# Lifecycle: Item

> Schema file: [lifecycle_item.yaml](./lifecycle_item.yaml)
> Initial State: available | Terminal States: sold, lost

## Sơ đồ vòng đời

```text
available -> reserved -> rented -> available
available -> sold
rented -> lost
reserved --(timeout)--> available
```

## Các trạng thái

| State       | Mô tả              | Terminal? | UI Label   | UI Color |
| ----------- | ------------------ | --------- | ---------- | -------- |
| available   | Sẵn sàng giao dịch | Không     | Sẵn sàng   | xanh     |
| reserved    | Đang giữ chỗ       | Không     | Đã giữ chỗ | vàng     |
| rented      | Đang thuê          | Không     | Đang thuê  | đỏ       |
| sold        | Đã bán             | Có        | Đã bán     | xám      |
| lost        | Bị mất             | Có        | Thất lạc   | đen      |
| maintenance | Chờ xử lý          | Không     | Bảo trì    | cam      |

## Chuyển trạng thái

| Từ        | Đến       | Kích hoạt bởi                | Điều kiện              | Event phát ra          |
| --------- | --------- | ---------------------------- | ---------------------- | ---------------------- |
| available | reserved  | bp_inventory-reserve-item_v1 | Item không bị lock     | item_status_changed    |
| reserved  | available | reservation_expire_job       | Hết hạn reservation    | reservation_expired    |
| reserved  | rented    | bp_rental-create-contract_v1 | Đúng customer/policy   | item_status_changed    |
| available | rented    | bp_rental-create-contract_v1 | Item sẵn sàng          | item_status_changed    |
| available | sold      | bp_pos-create-order_v1       | Payment hợp lệ         | item_status_changed    |
| rented    | available | bp_rental-return-items_v1    | Không bị lost          | item_condition_updated |
| rented    | lost      | bp_rental-return-items_v1    | condition_after = lost | item_status_changed    |

## Auto Transitions

| Từ       | Đến       | Trigger                            | Mô tả                          |
| -------- | --------- | ---------------------------------- | ------------------------------ |
| reserved | available | timeout theo reservation_expire_at | Tự release khi khách không lấy |

## Lưu ý cho Agent

- Luôn kiểm tra trạng thái item trước khi gọi API giao dịch.
- Nếu item đã `rented` hoặc `sold` thì chặn ngay luồng scan add vào giỏ.
- Với reservation hết hạn, ưu tiên kiểm tra realtime thay vì chỉ dựa vào cron cleanup.
