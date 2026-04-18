# Luồng Nghiệp Vụ: Unified POS (Zero-Click Checkout) & Quản Lý Kho Hỗn Hợp

Tài liệu này mô tả chi tiết cách hệ thống StoryHub gộp chung quá trình tính tiền (Bán & Thuê) vào một giao diện thu ngân duy nhất, cũng như cách hệ thống phân tách giữa hàng Mua Lẻ (Mới) và hàng Cho Thuê (SKU Vật Lý).

## 1. Giới Thiệu Sự Kiện (Business Context)

Thay vì thiết kế hệ thống POS rời rạc truyền thống (khách mua sách qua quầy 1, thuê sách qua quầy 2), StoryHub áp dụng **Unified Checkout**. Khi nhân viên quét mã vạch trên tay khách hàng mang đến, quầy Kiosk sẽ tự xác định thông tin này là bán lẻ (nguyên seal) hay là sách được cho thuê dựa vào định dạng Barcode.

### 1.1 Khái Niệm Tồn Kho "Kép"
- **Sách Mua Mới (Retail Stock):** Không tốn chi phí in tem nội bộ. Được theo dõi trực tiếp tại bảng `volume`. Định danh thông qua **ISBN** do Nhà xuất bản phát hành (ví dụ: `978-604-XXX`). Quét ISBN sẽ lấy trực tiếp thông tin Volume và trừ số lượng `retail_stock`.
- **Sách Cho Thuê (Rental Item/SKU):** Để tránh thất thoát, các ấn phẩm cho thuê buộc phải được quản lý 1-1 (1 dòng DB = 1 cuốn vật lý). Định danh bằng **Mã SKU riêng** có dán tem do cửa hàng tự in, luôn bắt đầu bằng chữ `RNT-` (Ví dụ: `RNT-11-FA42D1`). 

---

## 2. Luồng Sinh Mã Cho Thuê Từ Kho (Convert To Rental)

**Vấn đề:** Các nhà sách thường nhập về 100 cuốn mới. Ban đầu chúng chỉ nằm ở dạng "Bán Mới" (Retail Stock). Khi cửa hàng muốn trích 2 cuốn mang ra cho thuê, họ cần cấp danh tính độc lập (sinh mã RNT).

**Luồng hoạt động (Tab Inventory):**
1. Nhân viên tìm kiếm cuốn truyện qua ISBN trong màn hình Kho (Inventory). DB query ra dòng Volume.
2. Bấm "Chuyển ra Thuê", và nhập số lượng (`N`).
3. Backend gọi API `POST /api/v1/inventory/convert-to-rental`.
4. Logic xử lý:
   - Khoá transaction ngăn race condition.
   - Trừ `-N` số lượng `retail_stock` trong bảng `volume`.
   - Lặp `N` lần, tự động Insert vào bảng `item` với mã định dạng: `RNT-{volume_id}-{uuid6}` (Tình trạng ban đầu = 100%, Status = `available`).
5. Kết quả trả về danh sách các chuỗi SKU `RNT-`. Nhân viên đem danh sách này đi in tem dán lên gáy sách. Cửa hàng chính thức có `N` quyển sách thuê.

---

## 3. Luồng Checkout Gộp (Smart Unified POS)

Khi Khách Hàng (Customer) đến quầy thanh toán với 1 chồng sách trên tay (có thể lẫn sách mới và sách thuê).

### Quá trình Backend
1. Nhân viên quét liên tiếp (scan) toàn bộ mã vạch.
2. Form dữ liệu gửi lên API `POST /api/v1/checkout/unified` là một mảng `scanned_codes: ["978-604-123", "RNT-11-FA42D1", ...]`.
3. Backend xử lý vòng lặp để gộp giỏ hàng:
   - Kỹ thuật **Smart Routing**: 
     - Mã nào bắt đầu bằng `RNT-` hoặc `ITM-` 👉 Được phân loại vào mảng `rental_skus`.
     - Mã nào còn lại (ISBN) 👉 Được phân loại vào mảng `sales_isbns`.
4. Backend mở **1 Database Session Transaction duy nhất** để đảm bảo: tính trọn vẹn của giỏ. Nếu lỗi 1 cuốn, rollback toàn bộ, không bị treo bill lưng chừng.
5. **Xử lý Mảng Bán (`sales_isbns`)**:
   - Query xuống `volume`, trừ `retail_stock`. Nếu thiếu tồn kho, văng lỗi ngay (chống âm kho).
   - Cộng dồn doanh thu sách mới (dựa trên thuật toán tính `base_price`).
6. **Xử lý Mảng Thuê (`rental_skus`)**:
   - Yêu cầu bắt buộc phải có `customer_id` (Vì cho thuê cần danh tính để đòi sách). Báo lỗi nếu thu ngân quên. 
   - Đổi `status='rented'` trong `item` để khóa cuốn vật lý.
   - Tính toán phí thuê (tùy thuộc vào phần trăm hư hỏng nguyên bản của cuốn sách). Tính luôn **Tiền Cọc (Deposit)** mặc định tùy biến vào giá trị truyện.
7. **Xử lý hóa đơn hỗn hợp**:
   - Khởi tạo 1 Hóa Đơn Mua Hàng (`pos_order_id`) vào CSDL nếu có sách Bán.
   - Khởi tạo 1 Hợp Đồng Thuê Mượn (`rental_contract_id`) vào CSDL nếu có mảng Thuê.
   - Trả ra Grand Total gộp chung cả Tiền Sách Mới + Tiền Phí Thuê + Tiền Cọc Thuê. Thu ngân chỉ làm 1 việc duy nhất là thu tiền (không bấm chia 2 bill).

### Quá trình Frontend
- Ở `views/checkout.vue`, sử dụng Barcode Scanner Window Event Model (lắng nghe các máy tít nối USB qua event `storyhub:scan`).
- Mỗi lần Tít, check tính khả dụng rồi thả item vào mảng Vue Reactive Object `cart`.
- Giao diện có Conditional Render cho Tag UI (tự gán Tag `[Mua Mới]` hay `[Thuê]` để khách hàng nhìn thấy tường minh qua màn hình phụ).
- Ngay khi nhấn Hotkey `F1` hoặc `Enter`, lệnh API Checkout Unified được thực thi ngay lập tức. Thu ngân không cần chạm chuột, tăng mạnh Service Quality (Zero-Click Checkout Flow).

---

## 4. Lợi ích kỹ thuật
1. **Hiệu suất DB (Performance):** Tiết kiệm dung lượng lớn vì hàng ngàn cuốn truyện bán lẻ chỉ cần đúng phần đếm Int tại bảng `volume`.
2. **Khả năng Scaling:** Khi mảng Thuê lên đến quy mô lớn, bảng `item` chỉ quản lý các cuốn sách thật sự nhạy cảm, dễ bảo trì Indexing.
3. **An toàn Tài chính:** Mặc dù POS UI gộp làm 1, backend vẫn rạch ròi 2 bản ghi Transaction gốc (`pos_order` thuộc Sales vs `rental_contract` thuộc Services). Kế toán cuối ngày vẫn sẽ có báo cáo độc lập chuẩn xác 100% thay vì rườm rà gỡ rối tay.
