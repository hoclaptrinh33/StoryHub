# Hướng dẫn nhanh phím tắt vận hành (Phase 4)

## Phạm vi áp dụng

- Màn POS: [frontend/src/views/order-sale.vue](../../frontend/src/views/order-sale.vue)
- Màn Kiểm định trả: [frontend/src/views/rental-return-inspection.vue](../../frontend/src/views/rental-return-inspection.vue)
- Bộ lắng nghe phím toàn cục: [frontend/src/App.vue](../../frontend/src/App.vue)

## Bảng phím tắt chuẩn

| Phím    | Màn hình           | Tác dụng                                                     |
| ------- | ------------------ | ------------------------------------------------------------ |
| `F1`    | POS, Kiểm định trả | Xác nhận hành động chính (thanh toán hoặc kiểm tra/kết toán) |
| `Enter` | POS, Kiểm định trả | Tương đương `F1` khi không ở trong input text                |
| `Esc`   | POS, Kiểm định trả | Hủy phiên hiện tại (hủy giỏ hoặc reset phiên trả)            |
| `1`     | Kiểm định trả      | Gán condition item: `Tốt`                                    |
| `2`     | Kiểm định trả      | Gán condition item: `Hỏng nhẹ`                               |
| `3`     | Kiểm định trả      | Gán condition item: `Hỏng nặng`                              |
| `4`     | Kiểm định trả      | Gán condition item: `Mất`                                    |

## Quy tắc thao tác ngắn

1. Ưu tiên scanner trước, keyboard sau: quét mã liên tục, chỉ dùng chuột khi cần sửa ngoại lệ.
2. Với POS: sau khi quét đủ item, dùng `F1` hoặc `Enter` để thanh toán nhanh.
3. Với Kiểm định trả: quét hợp đồng, quét item, dùng `1/2/3/4` để đổi condition cho item đang chọn, sau đó bấm `F1` hoặc `Enter`.
4. Dùng `Esc` để hủy nhanh phiên thao tác khi cần làm lại từ đầu.

## Lưu ý chống xung đột phím

- Khi hệ thống đang nhận chuỗi scanner tốc độ cao, hotkey toàn cục sẽ được trì hoãn để tránh nhầm với ký tự quét.
- Khi đang mở modal xác nhận, hotkey toàn cục không ưu tiên kích hoạt.
- Nếu scanner không đẩy sự kiện (mất kết nối đầu đọc), có thể nhập tay mã và bấm `Enter` để xử lý cùng luồng.

## Checklist đào tạo 5 phút cho nhân viên mới

- [ ] Biết 3 phím cốt lõi `F1`, `Enter`, `Esc`.
- [ ] Thực hiện được 1 đơn POS không dùng chuột.
- [ ] Thực hiện được 1 phiên kiểm định trả có đổi condition bằng phím số.
- [ ] Biết reset phiên an toàn bằng `Esc` khi thao tác sai.
