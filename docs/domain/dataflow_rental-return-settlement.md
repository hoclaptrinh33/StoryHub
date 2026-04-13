# Data Flow: rental-return-settlement

## Tổng quan

Luồng dữ liệu trả truyện đi từ scanner input tại quầy tới settlement cuối cùng, đồng bộ sang CRM, inventory và báo cáo.

## Sơ đồ luồng

```text
[Barcode Scanner]
    |
    v
[UI Inspection Screen]
    |
    v
[bp_rental-return-items_v1]
    |
    +--> [Fee Engine]
    |
    +--> [Rental Settlement Write]
    |
    +--> [Item Status Update]
    |
    +--> [Event: rental_settled]
              |
              +--> [CRM debt/deposit update]
              +--> [Report aggregates update]
```

## Chi tiết từng bước

| Bước | API/Action                | Input                                 | Output               | Side Effects                              |
| ---- | ------------------------- | ------------------------------------- | -------------------- | ----------------------------------------- |
| 1    | Scanner capture           | barcode stream                        | item_id              | buffer và detect scanner                  |
| 2    | UI inspection             | item_id, contract context             | return_lines draft   | highlight item, chọn condition            |
| 3    | bp_rental-return-items_v1 | contract_id, return_lines, request_id | settlement response  | lock contract, validate item              |
| 4    | Fee engine                | return_lines + policy config          | fee breakdown        | tính late/damage/lost fee                 |
| 5    | Persistence               | settlement payload                    | settlement_id        | update rental_contract, rental_item, item |
| 6    | Event dispatch            | settlement result                     | rental_settled event | cập nhật CRM và report                    |

## Data Transformations

| Từ                    | Đến                    | Transformation                                                 |
| --------------------- | ---------------------- | -------------------------------------------------------------- |
| barcode raw string    | item_id                | trim + validate checksum hoặc pattern                          |
| return_lines + config | fee breakdown          | áp dụng policy theo condition và overdue                       |
| settlement totals     | customer finance delta | tính deducted_from_deposit, refund_to_customer, remaining_debt |

## Error Points

| Bước | Lỗi có thể            | Xử lý                            |
| ---- | --------------------- | -------------------------------- |
| 1    | scanner timeout       | reset buffer sau 50ms            |
| 3    | ITEM_NOT_IN_CONTRACT  | reject line và hiển thị lỗi đỏ   |
| 3    | RETURN_DUPLICATED     | bỏ qua line trùng, cảnh báo vàng |
| 4    | policy config missing | fallback rule mặc định           |
| 5    | lock conflict         | retry ngắn theo failure strategy |
