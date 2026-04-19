# logic_pricing-engine

## 1) Mục tiêu

Thiết kế Pricing Engine theo Phương án B để:

- quản lý hệ số giá tập trung bằng rule có version
- giữ snapshot giá giao dịch để báo cáo lịch sử không lệch
- cho phép override tại quầy có kiểm soát manager + audit

## 2) Nguồn dữ liệu định giá

- `volume.p_sell_new`: giá gốc duy nhất của tập truyện
- `price_rule`: cấu hình hệ số định giá theo phạm vi áp dụng
- `config_storyhub-runtime`: guardrails kiểm định độ hợp lý

Không lưu cứng giá thuê, cọc, giá truyện cũ ở bảng `volume`.

## 3) Công thức tính giá chuẩn

- Giá thuê:
  - `r_rent = round(p_sell_new * k_rent)`
- Giá cọc:
  - `d = max(d_floor, p_sell_new * k_deposit)`
- Giá bán truyện cũ:
  - `p_used = min(p_sell_new * f_condition * f_demand, p_sell_new * cap)`

Trong đó:

- `k_rent`, `k_deposit`, `d_floor`, `cap` lấy từ `price_rule` active
- `f_condition` lấy theo tình trạng item sau kiểm định
- `f_demand` lấy theo nhu cầu hoặc policy theo title/genre

## 4) Snapshot giao dịch (bắt buộc)

Khi tạo giao dịch bán hoặc thuê:

1. Hệ thống resolve rule active tại thời điểm xử lý.
2. Tính giá theo công thức.
3. Lưu cứng vào `order_item`:
   - `final_sell_price` hoặc
   - `final_rent_price` + `final_deposit` hoặc
   - `used_sale_price`
4. Gắn `price_rule_version` để truy vết.

Rule thay đổi về sau chỉ áp dụng giao dịch mới, không hồi tố snapshot cũ.

## 5) Override tại quầy (manager only)

### 5.1 Luồng UI

- Tại panel thanh toán có icon cây bút cạnh tổng tiền.
- Cashier bấm icon chỉ mở được màn xác thực manager.
- Manager quét thẻ hoặc nhập PIN.
- Popup sửa giá hiển thị:
  - `new_grand_total`
  - `reason_code` bắt buộc (dropdown)
  - `reason_note` tùy chọn

### 5.2 Luồng backend

- Xác thực `manager_approval_token` trước khi chấp nhận override.
- Validate biên độ override theo policy (`manager_price_override_min_ratio`).
- Lưu `price_override_flag = true` trong `order_item`.
- Ghi `audit_log` với action `POS_PRICE_OVERRIDE`.

## 6) Kiểm định hệ số trước khi kích hoạt rule

Trước khi đổi rule từ `draft` sang `active`, chạy mô phỏng trên tập dữ liệu đại diện:

- mẫu truyện giá thấp, trung bình, cao
- nhiều condition level khác nhau
- ít nhất 1 kịch bản truyện cũ có demand cao

Điều kiện pass:

- `r_rent / p_sell_new` nằm trong `[pricing_sanity_min_rent_ratio, pricing_sanity_max_rent_ratio]`
- `d / p_sell_new` nằm trong `[pricing_sanity_min_deposit_ratio, pricing_sanity_max_deposit_ratio]`
- `p_used / p_sell_new` nằm trong `[pricing_sanity_min_used_sale_ratio, pricing_sanity_max_used_sale_ratio]`
- Không tạo giá âm và không vi phạm cap của truyện cũ

Nếu fail:

- rule giữ nguyên trạng thái `draft`
- trả báo cáo cảnh báo để manager chỉnh hệ số

## 7) Quy trình vận hành đề xuất

1. Manager tạo rule mới ở trạng thái draft.
2. Chạy mô phỏng kiểm định hệ số.
3. Manager/owner duyệt rule.
4. Kích hoạt theo `valid_from`.
5. POS/Rental dùng rule active và lưu snapshot cho từng giao dịch.
