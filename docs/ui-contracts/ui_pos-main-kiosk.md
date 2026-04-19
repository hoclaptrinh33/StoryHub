# UI: PosMainKiosk

> Schema file: [ui_pos-main-kiosk.yaml](./ui_pos-main-kiosk.yaml)
> Page: /pos/main | Platform: kiosk

## Mô tả

Màn hình POS chính cho nhân viên quầy với mục tiêu thao tác nhanh hơn suy nghĩ, tối ưu cho scan barcode và keyboard-first.

## UI States

| State        | Khi nào                            | UI hiển thị                                        |
| ------------ | ---------------------------------- | -------------------------------------------------- |
| loading      | Vừa mở màn hình                    | Skeleton 3 cột, khóa thanh toán                    |
| success      | Sẵn sàng thao tác                  | Layout chuẩn scan hoặc tìm - giỏ hàng - thanh toán |
| error        | Lỗi API/scanner                    | Banner đỏ, nút thử lại, âm báo lỗi                 |
| empty        | Chưa có item                       | Hướng dẫn quét mã ngay giữa màn hình               |
| scanning     | Đang nhận chuỗi scanner            | Indicator scanning, khóa hotkey xung đột           |
| paying       | Đang tạo đơn                       | Overlay loading, disable mọi input                 |
| manager_auth | Đang xác thực manager cho override | Popup PIN hoặc quét thẻ manager, khóa submit chính |

## Data Binding

- Source: [bp_pos-create-order_v1.yaml](../api-reference/v1/bp_pos-create-order_v1.yaml)
- Refresh: manual
- Cache: none

### Field Mapping

| UI Field          | API Response Path                         | Format   |
| ----------------- | ----------------------------------------- | -------- |
| order_id          | response.order_id                         | string   |
| grand_total       | response.grand_total                      | currency |
| payment_breakdown | request.split_payments                    | array    |
| override_total    | request.checkout_override.new_grand_total | currency |

## User Interactions

| Hành động             | Trigger                             | API Call               | Optimistic? | Feedback                  |
| --------------------- | ----------------------------------- | ---------------------- | ----------- | ------------------------- |
| scan_item             | Global listener + Enter             | local lookup           | Có          | beep + highlight          |
| open_price_override   | Icon cây bút cạnh tổng tiền         | local modal state      | Có          | mở popup xác thực         |
| submit_price_override | Sau khi manager PIN hoặc thẻ hợp lệ | bp_pos-create-order_v1 | Không       | badge override + cảnh báo |
| create_order          | F1 hoặc nút Thanh toán              | bp_pos-create-order_v1 | Không       | redirect + toast          |
| clear_cart            | ESC                                 | local state            | Có          | inline message            |

## Error Handling (UI)

| Error Code                | UI Behavior       | Message                                | Action                |
| ------------------------- | ----------------- | -------------------------------------- | --------------------- |
| ITEM_NOT_AVAILABLE        | toast_error       | Truyện không sẵn sàng để bán           | highlight item        |
| SPLIT_PAYMENT_MISMATCH    | inline_validation | Tổng thanh toán chưa khớp              | focus panel           |
| ORDER_LOCK_CONFLICT       | retry_banner      | Xung đột dữ liệu, thử lại              | retry                 |
| NETWORK_ERROR             | retry_banner      | Mất kết nối backend cục bộ             | backoff retry         |
| MANAGER_APPROVAL_REQUIRED | modal_error       | Cần manager xác thực trước khi sửa giá | focus pin input       |
| OVERRIDE_REASON_REQUIRED  | inline_validation | Bắt buộc chọn lý do sửa giá            | focus reason dropdown |
| OVERRIDE_BELOW_FLOOR      | inline_validation | Giá override vượt quá biên độ cho phép | reset override        |

## Auth & Permissions (UI)

| Element                      | Rule                      | Khi không có quyền                                 |
| ---------------------------- | ------------------------- | -------------------------------------------------- |
| button_refund_order          | manager only              | ẩn                                                 |
| button_price_override_pencil | manager approval required | hiển thị nhưng bấm vào sẽ yêu cầu manager xác thực |
| input_price_override         | manager only              | disable                                            |
| select_override_reason       | manager only              | disable                                            |
| button_apply_manual_discount | cashier có giới hạn       | disable                                            |

## Responsive Behavior

| Breakpoint | Layout                  | Thay đổi                 |
| ---------- | ----------------------- | ------------------------ |
| Mobile     | Không hỗ trợ chính thức | hiển thị cảnh báo        |
| Tablet     | 2 cột                   | thu gọn panel thanh toán |
| Desktop    | 3 cột                   | vận hành chuẩn           |

## Performance Notes

- Bật virtualize list cho giỏ hàng dài.
- Dùng global listener + buffer timeout 50ms để phân biệt scanner/gõ tay.
- Prefetch dữ liệu CRM để giảm độ trễ lúc chọn khách.

## Wireframe / Mockup

- Trái: Scan hoặc tìm kiếm
- Giữa: Danh sách item trong giỏ
- Phải: Tổng tiền, icon cây bút override, discount, thanh toán
