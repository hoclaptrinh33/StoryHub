# StoryHub Frontend

Frontend shell cho StoryHub kiosk duoc xay dung voi Vue 3 + TypeScript + Vite.

## Chay local

```bash
npm install
npm run dev
```

Mac dinh frontend goi backend qua bien moi truong:

- `VITE_API_BASE_URL=http://127.0.0.1:8000`

Co the tao file `.env` tu `.env.example` neu can doi endpoint API.

## Chay Tauri desktop

```bash
npm run tauri:dev
```

## Build Tauri desktop

```bash
npm run tauri:build
```

```bash
# StoryHub

Hệ thống quản lý bán và cho thuê truyện dạng desktop kiosk, vận hành **local-first** và **offline-first**, được tối ưu hóa cho thao tác nhanh tại quầy cửa hàng.

---
```

```bash
## 1. Tổng quan
StoryHub bao gồm 6 khối nghiệp vụ chính được tích hợp hoàn chỉnh:

| STT | Khối chức năng | Vai trò |
| :--- | :--- | :--- |
| 1 | **Inventory** | Quản lý kho truyện |
| 2 | **CRM** | Quản lý khách hàng |
| 3 | **POS** | Bán hàng tại quầy |
| 4 | **Rental** | Cho thuê truyện |
| 5 | **Report** | Báo cáo & thống kê |
| 6 | **System** | Phân quyền, log, backup, tích hợp |

---
```

```bash
## 2. Chi tiết từng chức năng

### 2.1 Inventory — Quản lý kho
Truyện được tổ chức theo 3 tầng dữ liệu rõ ràng:
* **Title (Đầu truyện):** Thông tin chung về bộ truyện.
* **Volume (Tập):** Từng tập cụ thể trong bộ truyện.
* **Item (Cuốn vật lý):** Đơn vị thực tế để giao dịch (mọi thao tác thuê/bán đều thực hiện ở cấp này).

**Các chức năng chính:**
- Thêm, sửa, xóa thông tin theo cấu trúc cây: `Title` → `Volume` → `Item`.
- Tra cứu nhanh bằng mã vạch (Barcode) hoặc từ khóa tên.
- Theo dõi trạng thái Item thời gian thực: *Có sẵn, Đang được thuê, Đã bán, Đang giữ chỗ*.
- **Reservation:** Đặt giữ chỗ với thời gian hết hạn tự động (cron job dọn dẹp định kỳ).
- **Autofill:** Tự động điền thông tin đầu truyện từ metadata bên ngoài.

### 2.2 CRM — Quản lý khách hàng
- Tự động tạo mới hoặc cập nhật (**upsert**) thông tin khách hàng qua số điện thoại.
- Lưu trữ hồ sơ chi tiết: Tên, SĐT, địa chỉ, ghi chú đặc biệt.
- Truy xuất toàn bộ lịch sử giao dịch (mua/thuê) của từng khách hàng.
- Phân loại khách hàng để áp dụng các chính sách ưu đãi/thân thiết.

### 2.3 POS — Bán hàng tại quầy
Giao diện thiết kế theo layout 3 cột: **Scan/Tìm kiếm** — **Giỏ hàng** — **Thanh toán**.
- Quét mã vạch/tìm kiếm sản phẩm nhanh chóng.
- Tính tổng tiền tự động, hỗ trợ các loại mã giảm giá.
- **Price Snapshot:** Lưu giá tại thời điểm giao dịch (`final_sell_price`) để đảm bảo lịch sử không bị thay đổi khi bảng giá cập nhật.
- Hỗ trợ đa dạng phương thức (Tiền mặt / Chuyển khoản), tính tiền thừa cho khách.
- Chức năng hoàn trả đơn hàng (**Refund**).
- *Mục tiêu: Hoàn thành luồng thanh toán trong tối đa 3 bước.*

### 2.4 Rental — Cho thuê truyện
- **Hợp đồng thuê:** Gắn khách hàng, danh sách Item, ngày thuê và ngày trả dự kiến.
- **Snapshot tài chính:** Lưu giá thuê và tiền cọc tại thời điểm lập hợp đồng.
- **Quản lý trạng thái:** Theo dõi hợp đồng *Đang thuê, Quá hạn, Đã trả, Đã hủy*.
- Hỗ trợ gia hạn hợp đồng linh hoạt.
- **Xử lý trả sách:** Kiểm tra tình trạng sách, tính phí phạt trễ hạn, hoàn tiền cọc tự động.
- **Settlement:** Tự động tổng hợp toàn bộ khoản thu/hoàn sau khi kết thúc hợp đồng.
- Hệ thống cảnh báo hợp đồng sắp đến hạn và quá hạn.

### 2.5 Report — Báo cáo & Thống kê
- Theo dõi doanh thu theo thời gian (Ngày, Tuần, Tháng hoặc tùy chọn).
- Thống kê sản phẩm "Best-seller" và các đầu truyện được thuê nhiều nhất.
- **Báo cáo tồn kho:** Trạng thái Item thực tế trong kho.
- Danh sách các hợp đồng thuê quá hạn cần xử lý gấp.

### 2.6 System — Vận hành hệ thống
- **Phân quyền (RBAC):** Kiểm soát quyền hạn nhân viên chặt chẽ.
- **Audit log:** Ghi lại chi tiết mọi hành động (Before/After) và người thực hiện (Actor) để truy vết rủi ro.
- **Backup:** Sao lưu dữ liệu thủ công hoặc tự động theo lịch trình.
- **Soft delete:** Dữ liệu xóa được giữ lại để phục vụ audit, không xóa vật lý khỏi database.

---
```

```bash
## 3. Các ràng buộc kỹ thuật quan trọng

| Ràng buộc | Mục đích |
| :--- | :--- |
| **Transaction locking** | Ngăn chặn xung đột khi 2 người cùng thao tác trên 1 ItemId |
| **Idempotency** | Chống việc quét mã/click lặp gây nhân đôi giao dịch |
| **Snapshot giá** | Đảm bảo tính chính xác của lịch sử tài chính |
| **Reservation expiry** | Tự động giải phóng Item khi hết hạn giữ chỗ |
| **Realtime sync** | Đồng bộ trạng thái qua WebSocket gần như tức thời |
| **Offline-first** | Đảm bảo hệ thống vẫn chạy ổn định khi mất kết nối Internet |

---
```
```bash
## 4. Nguyên tắc giao diện (UX/UI)
- ⌨️ **Keyboard-first, mouse-optional:** Ưu tiên thao tác bàn phím để tối ưu tốc độ.
- 🔍 **Global barcode listener:** Nhận diện mã vạch mọi lúc (buffer ~50ms để phân biệt với gõ phím).
- 🔊 **Feedback đa giác quan:** Phản hồi qua màu sắc, âm thanh và highlight rõ ràng.
- ⚡ **Quy tắc 3 bước:** Mọi luồng thao tác chuẩn không vượt quá 3 bước thực hiện.

---

## 5. Kiến trúc kỹ thuật

* **Giao diện Desktop:** Vue 3 + Tauri
* **Backend API:** FastAPI (Python)
* **ORM:** SQLAlchemy
* **Cơ sở dữ liệu:** SQLite (Lộ trình nâng cấp lên SQLCipher để bảo mật)
* **Realtime:** WebSocket
* **Mô hình triển khai:** Offline-first, Local-first
```