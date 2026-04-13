# Domain: RentalContract

> Schema file: [domain_rental-contract.yaml](./domain_rental-contract.yaml)
> Bounded Context: rental | Aggregate Root: Yes

## Mô tả nghiệp vụ

RentalContract là nguồn sự thật cho toàn bộ vòng đời thuê gồm tạo hợp đồng, gia hạn, trả từng phần và tất toán cọc hoặc nợ.

## Invariants (Luật bất biến)

| #   | Quy tắc                                         | Enforced bởi        | Khi vi phạm               |
| --- | ----------------------------------------------- | ------------------- | ------------------------- |
| 1   | Contract active phải có ít nhất một rental_item | create contract API | EMPTY_RENTAL_CONTRACT     |
| 2   | Snapshot giá thuê và cọc bắt buộc               | create contract API | SNAPSHOT_MISSING          |
| 3   | Settlement không chứa số âm                     | return API          | INVALID_SETTLEMENT_AMOUNT |
| 4   | Contract closed không được mutate               | return/extend APIs  | CONTRACT_ALREADY_CLOSED   |

## Aggregate Structure

```text
RentalContract
├── RentalItem
└── RentalSettlement
```

## Relationships

| Entity liên quan | Kiểu quan hệ | Cascade  | Mô tả                            |
| ---------------- | ------------ | -------- | -------------------------------- |
| Customer         | many-to-one  | restrict | Contract thuộc một khách         |
| Item             | one-to-many  | restrict | Contract quản lý nhiều item thuê |

## Business Rules

| Quy tắc                   | Mô tả                  | Áp dụng cho        | Cấu hình được? |
| ------------------------- | ---------------------- | ------------------ | -------------- |
| Partial return allowed    | Trả nhiều lần hợp lệ   | return API         | Không          |
| Overdue and damage policy | Rule phí theo cửa hàng | return/extend APIs | Có             |

## Domain Events

| Event                   | Khi nào phát            | Consumers             |
| ----------------------- | ----------------------- | --------------------- |
| rental_contract_created | Tạo contract thành công | audit, CRM, report    |
| rental_item_returned    | Nhận trả item           | fee engine, inventory |
| rental_settled          | Kết toán xong           | report, debt ledger   |
| rental_extended         | Gia hạn thành công      | notification, audit   |

## APIs liên quan

| API                          | Hành động     | Invariants liên quan |
| ---------------------------- | ------------- | -------------------- |
| bp_rental-create-contract_v1 | Tạo hợp đồng  | 1, 2                 |
| bp_rental-return-items_v1    | Trả và settle | 3, 4                 |
| bp_rental-extend-contract_v1 | Gia hạn       | 4                    |
