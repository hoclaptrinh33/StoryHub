# logic_rental-lifecycle

## 1) Mục tiêu

Chuẩn hóa vòng đời thuê để:

- thao tác nhanh ở quầy
- tính phí chính xác
- không thất thoát cọc
- xử lý được trả thiếu, mất truyện, và gia hạn

## 2) Luồng tạo phiếu thuê

1. Nhân viên chọn khách hàng
2. Quét item vào phiếu thuê
3. Hệ thống lock item theo transaction
4. Snapshot giá thuê và cọc cho từng item (`final_rent_price`, `final_deposit`)
5. Tạo contract + rental_item
6. Chuyển item `available/reserved -> rented`

## 3) Luồng trả truyện

1. Quét item trả
2. Đối chiếu item thuộc contract nào
3. Chọn trạng thái kiểm định sau trả: `good|minor_damage|major_damage|lost`
4. Tính phí tự động:
   - phí thuê
   - phí quá hạn
   - phí hỏng
   - phí mất
5. Khấu trừ từ cọc
6. Hoàn tiền hoặc ghi nợ
7. Cập nhật contract sang `partial_returned` hoặc `closed`

## 4) Luồng gia hạn

1. Chọn contract đang `active` hoặc `overdue`
2. Kiểm tra điều kiện cho gia hạn
3. Cập nhật `due_date` mới
4. Nếu cần, thu thêm cọc
5. Ghi audit log trước/sau

## 5) State machine đề xuất

### rental_contract.status

- `active`
- `partial_returned`
- `overdue`
- `closed`
- `cancelled`

### rental_item.status

- `rented`
- `returned`
- `lost`

## 6) Quy tắc nghiệp vụ quan trọng

- Không cho trả item không thuộc contract
- Không cho trả trùng cùng item trong một lần settle
- Khi item mất: không đưa lại `available`, trạng thái item phải thành `lost`
- Không cho phí âm hoặc tổng settle âm
- Một request settle chỉ xử lý một lần theo `request_id`

## 7) Công thức tham chiếu

- `total_fee = rental_fee + late_fee + damage_fee + lost_fee`
- `deducted_from_deposit = min(total_fee, remaining_deposit)`
- `refund_to_customer = max(remaining_deposit - total_fee, 0)`
- `remaining_debt = max(total_fee - remaining_deposit, 0)`

## 8) Điểm cần test thực tế

- Trả một phần nhiều lần
- Trả vượt hạn nhiều ngày
- Mất item + còn item khác trả bình thường
- Gia hạn nhiều lần liên tiếp
- Scan nhầm item không thuộc contract
