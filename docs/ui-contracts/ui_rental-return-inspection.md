# UI: RentalReturnInspection

> Schema file: [ui_rental-return-inspection.yaml](./ui_rental-return-inspection.yaml)
> Page: /rental/return | Platform: kiosk

## Mô tả

Màn hình trả truyện tập trung vào tốc độ: scan item, chọn tình trạng bằng phím số, tính phí realtime và xác nhận settlement.

## UI States

| State    | Khi nào                       | UI hiển thị                      |
| -------- | ----------------------------- | -------------------------------- |
| loading  | Mở màn hình hoặc đổi contract | Skeleton danh sách + panel phí   |
| success  | Contract hợp lệ               | Hiển thị line trả, breakdown phí |
| error    | Contract/API lỗi              | Fullpage error hoặc banner       |
| empty    | Chưa scan item nào            | Hướng dẫn scan item              |
| settling | Đang gửi settle               | Overlay loading, khóa input      |

## Data Binding

- Source: [bp_rental-return-items_v1.yaml](../api-reference/v1/bp_rental-return-items_v1.yaml)
- Refresh: manual
- Cache: none

### Field Mapping

| UI Field              | API Response Path              | Format   |
| --------------------- | ------------------------------ | -------- |
| total_fee             | response.total_fee             | currency |
| deducted_from_deposit | response.deducted_from_deposit | currency |
| refund_to_customer    | response.refund_to_customer    | currency |
| remaining_debt        | response.remaining_debt        | currency |

## User Interactions

| Hành động           | Trigger                 | API Call                  | Optimistic? | Feedback         |
| ------------------- | ----------------------- | ------------------------- | ----------- | ---------------- |
| scan_return_item    | Global scanner          | local match               | Có          | beep + highlight |
| set_condition_quick | Phím 1/2/3/4            | local state               | Có          | inline update    |
| submit_settlement   | Enter hoặc nút xác nhận | bp_rental-return-items_v1 | Không       | toast kết quả    |

## Error Handling (UI)

| Error Code                   | UI Behavior       | Message                   | Action             |
| ---------------------------- | ----------------- | ------------------------- | ------------------ |
| CONTRACT_NOT_FOUND           | fullpage_error    | Không tìm thấy phiếu thuê | quay về tìm kiếm   |
| ITEM_NOT_IN_CONTRACT         | toast_error       | Item không thuộc phiếu    | reject item        |
| RETURN_DUPLICATED            | inline_warning    | Item đã trả trước đó      | đánh dấu duplicate |
| INVALID_CONDITION_TRANSITION | inline_validation | Condition không hợp lệ    | yêu cầu chọn lại   |

## Auth & Permissions (UI)

| Element                     | Rule         | Khi không có quyền |
| --------------------------- | ------------ | ------------------ |
| button_override_fee         | manager only | ẩn                 |
| input_manual_fee_adjustment | manager only | disable            |

## Responsive Behavior

| Breakpoint | Layout                          | Thay đổi           |
| ---------- | ------------------------------- | ------------------ |
| Mobile     | Không hỗ trợ                    | cảnh báo           |
| Tablet     | item list trên, settlement dưới | giữ phím tắt chính |
| Desktop    | 2 cột                           | vận hành chính     |

## Performance Notes

- Mặc định condition là `good`, nhân viên đổi nhanh bằng phím số.
- Panel settlement cập nhật tức thì để tránh tính tay.
- Không dùng popup xác nhận nhiều bước trong flow trả chuẩn.

## Wireframe / Mockup

- Trái: danh sách item vừa scan + condition badge
- Phải: breakdown phí, tiền cọc trừ, tiền hoàn hoặc nợ còn lại
