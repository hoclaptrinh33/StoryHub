# Domain: Item

> Schema file: [domain_item.yaml](./domain_item.yaml)
> Bounded Context: inventory-rental-pos | Aggregate Root: Yes

## Mô tả nghiệp vụ

Item là đơn vị vật lý duy nhất được phép đi qua các luồng giữ chỗ, bán, thuê, trả và kiểm định.

## Invariants (Luật bất biến)

| #   | Quy tắc                                                | Enforced bởi          | Khi vi phạm          |
| --- | ------------------------------------------------------ | --------------------- | -------------------- |
| 1   | Item phải thuộc một volume hợp lệ                      | database/service      | ITEM_VOLUME_REQUIRED |
| 2   | Item chỉ có một trạng thái hoạt động tại một thời điểm | API reserve/sell/rent | ITEM_STATE_CONFLICT  |
| 3   | Không giao dịch khi item không sẵn sàng                | POS/Rental APIs       | ITEM_NOT_AVAILABLE   |
| 4   | Reservation luôn có expiry realtime                    | Inventory reserve API | RESERVATION_EXPIRED  |

> Agent phải kiểm tra invariants trước khi gọi API mutation.

## Aggregate Structure

```text
Item
├── ItemReservation
└── ItemConditionTimeline
```

## Relationships

| Entity liên quan | Kiểu quan hệ | Cascade  | Mô tả                              |
| ---------------- | ------------ | -------- | ---------------------------------- |
| Volume           | many-to-one  | restrict | Nhiều item cùng thuộc một volume   |
| RentalContract   | many-to-many | restrict | Item có lịch sử thuê theo hợp đồng |
| PosOrder         | many-to-one  | restrict | Item chỉ được bán một lần          |

## Business Rules

| Quy tắc                | Mô tả                                                       | Áp dụng cho       | Cấu hình được? |
| ---------------------- | ----------------------------------------------------------- | ----------------- | -------------- |
| Reservation conversion | reserved chuyển thành sold hoặc rented khi giao dịch hợp lệ | reserve/sell/rent | Có             |
| Condition downgrade    | trả item có thể giảm health_percent                         | rental return     | Có             |

## Domain Events

| Event                  | Khi nào phát        | Consumers                   |
| ---------------------- | ------------------- | --------------------------- |
| item_status_changed    | Item đổi trạng thái | UI realtime, audit, báo cáo |
| reservation_expired    | Reservation quá hạn | inventory service, UI       |
| item_condition_updated | Kiểm định sau trả   | fee engine, audit           |

## APIs liên quan

| API                          | Hành động             | Invariants liên quan |
| ---------------------------- | --------------------- | -------------------- |
| bp_inventory-reserve-item_v1 | Giữ chỗ item          | 2, 4                 |
| bp_pos-create-order_v1       | Bán item              | 2, 3                 |
| bp_rental-create-contract_v1 | Thuê item             | 2, 3                 |
| bp_rental-return-items_v1    | Trả và kiểm định item | 2, condition rule    |
