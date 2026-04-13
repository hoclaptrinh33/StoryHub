# logic_barcode-keyboard-buffer

## 1) Mục tiêu

Máy quét barcode hoạt động như bàn phím tốc độ cao. Hệ thống cần bắt được mã quét ở mọi màn hình mà không cần focus vào input.

## 2) Thiết kế listener

- Dùng global key listener ở cấp app shell
- Buffer ký tự theo thời gian thực
- Gặp `Enter` thì đóng gói thành một lần scan
- Timeout buffer ~50ms để reset chuỗi

## 3) Phân biệt scanner và gõ tay

Heuristic đề xuất:

- Nếu chuỗi có độ dài >= 8
- Và khoảng cách giữa các phím <= 30ms liên tiếp
- Và kết thúc bằng Enter

=> coi là scanner input.

Nếu không đạt điều kiện thì xử lý như keyboard bình thường.

## 4) Chống xung đột hotkey

Khi buffer scanner đang active:

- tạm khóa các hotkey toàn cục (F1, ESC, Ctrl+...)
- chỉ xử lý scanner pipeline
- sau khi complete/fail thì mở lại hotkey

## 5) UX feedback bắt buộc

Mỗi lần scan thành công:

- phát âm thanh `beep`
- highlight item vừa thêm 600-1000ms
- hiển thị toast xanh ngắn gọn

Mỗi lần scan lỗi:

- âm thanh cảnh báo khác
- toast đỏ có lý do lỗi (item không tồn tại, item đã thuê, item bị lock)

## 6) Pseudo-flow

```text
onKeyDown(event):
  if scannerSessionActive then disableHotkeys()
  append event.key vào buffer
  if timeout > 50ms then reset buffer
  if key == Enter:
    if isScannerPattern(buffer):
      emit SCAN_COMPLETED(bufferWithoutEnter)
      reset buffer
      enableHotkeys()
    else:
      pass-through keyboard event
```

## 7) Các case cần test

- Quét liên tục 20 mã trong 1 phút
- Quét khi focus đang ở modal khác
- Người dùng gõ tay nhanh nhưng không phải barcode
- Mất kết nối scanner giữa chừng
