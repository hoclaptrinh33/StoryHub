# Tiêu chuẩn tra cứu thuật ngữ StoryHub

> Loại tài liệu: Standard
> Trạng thái: active
> Phiên bản: 1.0.0

## 1) Mục tiêu

Tài liệu này chuẩn hóa cách dùng thuật ngữ trong toàn bộ dự án StoryHub để giảm hiểu sai giữa PM, Backend, Frontend, QA và vận hành.

Mọi tài liệu mới (API, domain, UI flow, test case) nên ưu tiên dùng đúng thuật ngữ trong glossary này.

## 2) Cách tra cứu chuẩn

1. Xác định ngữ cảnh: dữ liệu, API, UI hay vận hành.
2. Tra thuật ngữ trong bảng chuẩn bên dưới.
3. Nếu cùng ý nghĩa nhưng khác cách gọi, dùng cột "Không dùng thay thế" để chuẩn hóa lại.
4. Khi chưa có thuật ngữ phù hợp, thêm mục mới theo quy trình ở phần 4.

## 3) Bảng thuật ngữ chuẩn

| Thuật ngữ chuẩn     | Định nghĩa ngắn                                             | Dùng trong ngữ cảnh            | Không dùng thay thế                    |
| ------------------- | ----------------------------------------------------------- | ------------------------------ | -------------------------------------- |
| Title               | Đầu truyện, nhóm nội dung cấp cao nhất                      | Domain model, metadata         | "Sản phẩm truyện"                      |
| Volume              | Tập thuộc một Title                                         | Domain model, tồn kho          | "Quyển" (khi đang nói tầng dữ liệu)    |
| Item                | Bản sao vật lý có barcode để thuê/bán                       | POS, Rental, Inventory         | "Sách" chung chung                     |
| Reservation         | Trạng thái giữ chỗ tạm thời cho Item                        | Inventory, POS, Rental         | "Đặt cọc"                              |
| Reservation Expiry  | Thời điểm hết hiệu lực giữ chỗ                              | Inventory logic, cron cleanup  | "Timeout đơn"                          |
| Rental Contract     | Hợp đồng thuê gồm danh sách Item và điều khoản phí/cọc      | Rental module                  | "Đơn thuê" (nếu là tên field kỹ thuật) |
| Settlement          | Bước kết toán khi trả truyện, gồm phí phát sinh và hoàn cọc | Rental return flow, finance    | "Chốt đơn trả"                         |
| Lock Conflict       | Xung đột khi 2 thao tác cùng chiếm quyền trên một Item      | API error, UI cảnh báo         | "Lỗi bận"                              |
| Idempotency         | Cơ chế chống xử lý trùng với cùng request_id                | API side effects               | "Retry-safe" (nếu không giải thích)    |
| Price Snapshot      | Giá/cọc được chụp tại thời điểm giao dịch                   | POS, Rental, Report            | "Giá hiện tại"                         |
| Price Rule          | Bộ hệ số định giá có version và thời gian hiệu lực          | Pricing engine, manager config | "Bảng giá cứng"                        |
| Pricing Engine      | Thành phần tính giá thuê, cọc, truyện cũ từ rule active     | POS, Rental, Report            | "Tính tay"                             |
| Order Item Snapshot | Dòng dữ liệu lưu cứng giá cuối ở thời điểm giao dịch        | POS, Rental, finance           | "Giá tạm"                              |
| Price Override      | Hành động manager chỉnh giá tại quầy cho một giao dịch      | POS checkout                   | "Giảm tạm"                             |
| Override Reason     | Mã lý do bắt buộc khi override giá                          | Audit, compliance              | "Ghi chú cho có"                       |
| Soft Delete         | Đánh dấu xóa logic để giữ lịch sử                           | Database, audit                | "Xóa cứng"                             |
| Audit Log           | Nhật ký before/after kèm actor cho thao tác quan trọng      | Security, compliance           | "Log thường"                           |
| Return Inspection   | Bước kiểm tra tình trạng Item lúc trả                       | UI contract, rental return     | "Check hàng"                           |
| Branch              | Đơn vị cửa hàng/chi nhánh vận hành                          | Access scope, reporting        | "Shop" (trong tên field kỹ thuật)      |

## 4) Quy tắc thêm thuật ngữ mới

- Bắt buộc thêm 4 thông tin: tên chuẩn, định nghĩa, ngữ cảnh dùng, từ thay thế không nên dùng.
- Nếu thuật ngữ ảnh hưởng API contract, cập nhật đồng thời file `.md` và `.yaml` liên quan.
- Nếu thuật ngữ ảnh hưởng UI label quan trọng, cập nhật UI contract và user flow liên quan.

## 5) Quy tắc cập nhật và phê duyệt

- Owner chính: Tech Lead hoặc người phụ trách module bị ảnh hưởng.
- Reviewer bắt buộc: đại diện ít nhất 2 nhóm (ví dụ Backend + Frontend, hoặc PM + QA).
- Mọi thay đổi phải ghi vào changelog của dự án nếu ảnh hưởng hành vi hoặc cách hiểu nghiệp vụ.
