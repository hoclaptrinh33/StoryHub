# Lifecycle: RentalContract

> Schema file: [lifecycle_rental-contract.yaml](./lifecycle_rental-contract.yaml)
> Initial State: active | Terminal States: closed, cancelled

## Sơ đồ vòng đời

```text
active -> partial_returned -> closed
active -> overdue -> partial_returned -> closed
active --(extend)--> active
active -> closed
```

## Các trạng thái

| State            | Mô tả        | Terminal? | UI Label      | UI Color |
| ---------------- | ------------ | --------- | ------------- | -------- |
| active           | Còn hiệu lực | Không     | Đang hiệu lực | xanh     |
| partial_returned | Trả một phần | Không     | Trả một phần  | vàng     |
| overdue          | Quá hạn      | Không     | Quá hạn       | đỏ       |
| closed           | Đã tất toán  | Có        | Đã đóng       | xám      |
| cancelled        | Đã hủy       | Có        | Đã hủy        | đen      |

## Chuyển trạng thái

| Từ               | Đến              | Kích hoạt bởi                | Điều kiện             | Event phát ra         |
| ---------------- | ---------------- | ---------------------------- | --------------------- | --------------------- |
| active           | partial_returned | bp_rental-return-items_v1    | Còn item chưa trả     | rental_item_returned  |
| active           | closed           | bp_rental-return-items_v1    | Trả đủ và settle xong | rental_settled        |
| partial_returned | closed           | bp_rental-return-items_v1    | Trả hết item còn lại  | rental_settled        |
| active           | overdue          | overdue_monitor_job          | quá due_date          | rental_overdue_marked |
| overdue          | partial_returned | bp_rental-return-items_v1    | trả được một phần     | rental_item_returned  |
| overdue          | closed           | bp_rental-return-items_v1    | trả đủ và settle xong | rental_settled        |
| active           | active           | bp_rental-extend-contract_v1 | due_date mới hợp lệ   | rental_extended       |

## Auto Transitions

| Từ     | Đến     | Trigger      | Mô tả                        |
| ------ | ------- | ------------ | ---------------------------- |
| active | overdue | cron mỗi giờ | Tự đánh dấu hợp đồng quá hạn |

## Lưu ý cho Agent

- Trước khi gọi `bp_rental-extend-contract_v1`, phải xác thực contract chưa ở terminal state.
- Luồng trả truyện cần branch rõ giữa `partial_returned` và `closed` để tính phí chính xác.
- Nếu contract đã `closed` thì chặn mọi mutation tiếp theo.
