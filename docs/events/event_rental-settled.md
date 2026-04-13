# Event: rental_settled

> Schema file: [event_rental-settled.yaml](./event_rental-settled.yaml)
> Domain: rental | Severity: critical

## Mô tả

Sự kiện được phát sau khi hệ thống kết toán trả truyện xong, dùng để đồng bộ tài chính khách hàng và số liệu báo cáo.

## Trigger

- Phát bởi: `bp_rental-return-items_v1`
- Điều kiện: settlement tạo thành công.

## Payload

| Field                 | Kiểu      | Bắt buộc | Mô tả            |
| --------------------- | --------- | -------- | ---------------- |
| settlement_id         | string    | Có       | Mã settlement    |
| contract_id           | string    | Có       | Mã hợp đồng thuê |
| customer_id           | string    | Có       | Mã khách         |
| total_fee             | number    | Có       | Tổng phí         |
| deducted_from_deposit | number    | Có       | Số tiền trừ cọc  |
| refund_to_customer    | number    | Có       | Số tiền hoàn lại |
| remaining_debt        | number    | Có       | Nợ còn lại       |
| settled_at            | date-time | Có       | Thời điểm settle |

## Consumers

| Consumer                | Hành động             | Async | Bắt buộc | Khi fail |
| ----------------------- | --------------------- | ----- | -------- | -------- |
| update_customer_finance | Cập nhật debt/cọc CRM | Không | Có       | retry    |
| push_report_aggregates  | Cập nhật báo cáo      | Có    | Không    | retry    |
| notify_cashier_ui       | Phản hồi UI tại quầy  | Có    | Không    | skip     |

## Luồng xử lý

```text
return API -> rental_settled
  -> update_customer_finance
  -> push_report_aggregates
  -> notify_cashier_ui
```

## Lưu ý

- Event này cần độ tin cậy cao vì ảnh hưởng tài chính.
- Consumer tài chính nên xử lý theo transaction hoặc outbox pattern.
