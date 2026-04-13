```text
📚 Hệ Thống Quản Lý Cửa Hàng Bán & Cho Thuê Truyện

Báo cáo Tuần 1 — Mô tả chức năng & Phác thảo giao diện
Môn học: Lập trình ứng dụng | Nhóm: Lê Hải Đăng & Lê Quân (20233202)


👥 Thông Tin Nhóm
Thành viênMã SVVai tròLê Hải Đăng—Trưởng nhóm · Khởi tạo dự án, thiết lập môi trường, định hướng Source CodeLê Quân20233202Viết tài liệu đặc tả, vẽ ERD, Use Case, thiết kế UI/MockupLê Văn Đức—Thành viên · (Bạn có thể bổ sung vai trò cụ thể)

📋 Mục Lục

Tổng quan dự án
Yêu cầu chức năng
Yêu cầu phi chức năng
Thiết kế UI — Wireframe & Mockup
Sơ đồ Use Case
Công nghệ sử dụng
Cấu trúc thư mục
Tài liệu đính kèm


1. Tổng Quan Dự Án
Ứng dụng quản lý cửa hàng bán và cho thuê truyện được xây dựng nhằm số hóa toàn bộ quy trình vận hành của một cửa hàng truyện truyền thống, bao gồm:

Quản lý kho truyện theo thời gian thực
Xử lý giao dịch bán hàng tại quầy (Point of Sale)
Quản lý vòng đời thuê truyện (tạo phiếu → trả → tính phạt)
Lưu trữ và phân hạng khách hàng
Thống kê & báo cáo doanh thu

Đối tượng sử dụng: Nhân viên bán hàng (Staff) và Quản trị viên (Admin) tại cửa hàng truyện vừa và nhỏ.

2. Yêu Cầu Chức Năng (Functional Requirements)
2.1 Module Quản Lý Truyện (Inventory Management)
Chức năngMô tảThêm truyện mớiNhập thông tin: tên, tác giả, nhà xuất bản, thể loại, số lượng, giá bán, giá thuêChỉnh sửa thông tinCập nhật bất kỳ trường dữ liệu nào của một đầu truyệnXóa truyệnXóa mềm (đánh dấu ngừng kinh doanh), không xóa cứng khỏi CSDLPhân loạiQuản lý theo thể loại, tác giả, nhà xuất bảnTheo dõi trạng tháiTự động cập nhật: Còn hàng / Đang cho thuê / Hết hàngTìm kiếm & lọcTra cứu nhanh theo tên, thể loại, trạng thái hoặc mã truyện

2.2 Module Quản Lý Bán Hàng (Point of Sale)
Chức năngMô tảTạo đơn hàngThêm / bớt sản phẩm vào giỏ hàng, điều chỉnh số lượngTính tiền tự độngTự động tổng hợp giá, áp dụng mã khuyến mãi (nếu có)Phương thức thanh toánHỗ trợ ghi nhận: Tiền mặt, Chuyển khoảnXuất hóa đơnIn hóa đơn bán hàng cho khách tại quầyCập nhật tồn khoTự động trừ số lượng sau khi thanh toán thành công

2.3 Module Quản Lý Cho Thuê (Rental Management)
Chức năngMô tảTạo phiếu thuêGhi nhận: khách hàng, truyện thuê, ngày bắt đầu, số ngày thuêTính tiền cọcHệ thống tự tính tiền cọc theo quy định cửa hàngQuy định ngày trảTự động xác định ngày đến hạnTrả truyệnCập nhật trạng thái, đối chiếu tình trạng truyện khi nhận lạiTính phí phạtTự tính phạt dựa trên số ngày trễ hạnHoàn / cấn trừ cọcXử lý tiền cọc tùy theo tình trạng: nguyên vẹn, hư hỏng, mất mát

2.4 Module Quản Lý Khách Hàng (Customer Management)
Chức năngMô tảThêm / cập nhật khách hàngLưu trữ: họ tên, SĐT, địa chỉ, ghi chúLịch sử giao dịchXem chi tiết lịch sử mua hàng và thuê truyện của từng kháchPhân hạng khách hàngTự động xếp hạng Thường / VIP theo tần suất và tổng chi tiêuCảnh báo quá hạnGắn cờ cảnh báo cho khách đang có phiếu thuê trễ hạn

2.5 Module Báo Cáo & Thống Kê (Reports)
Chức năngMô tảDoanh thu theo ngày/thángTách biệt doanh thu bán và doanh thu cho thuêTruyện HotLiệt kê top truyện được thuê/mua nhiều nhấtKhách hàng thân thiếtDanh sách khách VIP và tổng giá trị giao dịchTồn khoBáo cáo số lượng nhập/xuất và hàng tồn hiện tại

2.6 Module Phân Quyền & Bảo Mật (Access Control)
Vai tròQuyền hạnAdminToàn quyền: quản lý truyện, khách hàng, nhân viên, xem báo cáo, cấu hình hệ thốngStaffBán hàng, tạo phiếu thuê, xử lý trả truyện, tra cứu khách hàng

Audit log: Ghi lại toàn bộ hoạt động của từng tài khoản để tránh gian lận.
Mật khẩu được mã hóa trước khi lưu vào cơ sở dữ liệu.


3. Yêu Cầu Phi Chức Năng (Non-Functional Requirements)
Tiêu chíYêu cầuHiệu năngThời gian phản hồi các thao tác cơ bản < 2 giâyTính khả dụngGiao diện trực quan, nhân viên mới có thể thao tác cơ bản sau < 30 phút làm quenBảo mậtMật khẩu được hash (bcrypt), phân quyền rõ ràng theo vai tròTương thíchChạy ổn định trên Windows 10 trở lênĐộ tin cậyDữ liệu không bị mất khi tắt đột ngột (commit transaction)Bảo trìCode được tổ chức theo mô hình MVC, dễ mở rộng thêm module
```

```bash
4. Thiết Kế UI — Wireframe & Mockup
Giao diện được thiết kế theo tiêu chí tối giản, thao tác nhanh — ưu tiên cho nhân viên thu ngân làm việc trong môi trường bận rộn.

Màn hình 1 — Đăng Nhập (Login)

┌─────────────────────────────────┐
│         TruyenShop              │
│    Hệ thống quản lý cửa hàng    │
│                                 │
│  Tên đăng nhập: [____________]  │
│  Mật khẩu:      [____________]  │
│                                 │
│         [ Đăng nhập ]           │
│                                 │
│     Phân quyền: Admin / Staff   │
└─────────────────────────────────┘

Mô tả: Màn hình khởi động ứng dụng. Nhân viên nhập tài khoản, hệ thống xác thực và điều hướng đến Dashboard tương ứng với quyền hạn.
```

```bash
Màn hình 2 — Dashboard (Tổng quan)
┌──────────────────────────────────────────────────────────┐
│  [KPI] Tổng truyện  │ Đang thuê │ Doanh thu hôm nay │ KH│
├──────────────────────┬───────────────────────────────────┤
│  ⚠ Cảnh báo quá hạn │  Biểu đồ doanh thu 7 ngày        │
│  • Khách A — 2 ngày │                                   │
│  • Khách B — 1 ngày │  Giao dịch gần nhất               │
│                      │  • 14:32 - Bán - 85,000đ         │
│  🔥 Truyện Hot       │  • 13:15 - Thuê - 30,000đ        │
│  1. Conan T.100      │                                   │
└──────────────────────┴───────────────────────────────────┘
Mô tả: Trang chủ sau khi đăng nhập. Hiển thị 4 chỉ số KPI, danh sách cảnh báo truyện quá hạn, biểu đồ doanh thu và giao dịch mới nhất.
```

```bash
Màn hình 3 — Quản Lý Kho Truyện
┌──────────────────────────────────────────────────────────┐
│  [ Tìm kiếm: tên, thể loại... ]  [ Lọc ]  [+ Thêm mới] │
├──────┬──────────────┬──────────┬─────────┬───────┬───────┤
│ Mã   │ Tên truyện   │ Thể loại │ Giá bán │ Thuê  │ TT    │
├──────┼──────────────┼──────────┼─────────┼───────┼───────┤
│ T001 │ Conan T.100  │ Trinh th.│ 45,000đ │5,000đ │ ✅    │
│ T002 │ Naruto T.72  │ Hành đ.  │ 38,000đ │4,000đ │ 🟡    │
│ T003 │ Dragon Ball  │ Hành đ.  │ 50,000đ │5,000đ │ ❌    │
└──────┴──────────────┴──────────┴─────────┴───────┴───────┘
  Trạng thái: ✅ Còn hàng   🟡 Đang thuê   ❌ Hết hàng
Mô tả: Giao diện dạng bảng (Data Grid). Tích hợp tìm kiếm, lọc theo thể loại/trạng thái, nút thêm mới và chỉnh sửa từng dòng.
```

```bash
Màn hình 4 — Bán Hàng / Cho Thuê (Split-screen)
┌──────────────────────┬───────────────────────────────────┐
│   CHỌN TRUYỆN        │   GIỎ HÀNG                        │
│                      │                                   │
│ [ Tìm truyện... ]    │  Conan T.100 x1 ......... 45,000đ│
│                      │  Doraemon T.45 x2 ........ 56,000đ│
│ • Conan T.100  [+]   │                                   │
│ • One Piece    [+]   │  Mã KM: [__________]              │
│ • Doraemon     [+]   │  ─────────────────────────────    │
│ • Naruto  🟡   [—]   │  Tổng cộng:          101,000đ    │
│                      │  TT: Tiền mặt / CK                │
│                      │  [ Thanh toán & In hóa đơn ]      │
└──────────────────────┴───────────────────────────────────┘
Mô tả: Giao diện chia đôi màn hình. Bên trái chọn truyện, bên phải là giỏ hàng với tổng tiền, mã khuyến mãi và nút thanh toán. Có tab chuyển đổi giữa chế độ Bán và Cho thuê.
```

```bash
Màn hình 5 — Quản Lý Khách Hàng
┌──────────────────────────────────────────────────────────┐
│  [ Tìm khách hàng... ]                 [+ Thêm khách]   │
├───┬──────────────┬─────────────┬───────┬──────────┬──────┤
│ # │ Họ tên       │ SĐT         │ Hạng  │ Chi tiêu │      │
├───┼──────────────┼─────────────┼───────┼──────────┼──────┤
│ 1 │ Nguyễn V. An │ 0912 345 678│ VIP   │ 1,250,000│[Xem] │
│ 2 │ Trần Thị Cúc │ 0987 654 321│ Thường│   420,000│[Xem] │
│ 3 │ Lê Minh Đức  │ 0901 111 222│ VIP ⚠│ 2,100,000│[Xem] │
└───┴──────────────┴─────────────┴───────┴──────────┴──────┘
  ⚠ = Đang có phiếu thuê quá hạn
Mô tả: Danh sách khách hàng với badge phân hạng (Thường / VIP) và cờ cảnh báo quá hạn. Nút Xem mở chi tiết lịch sử giao dịch của từng cá nhân.
```

```bash
Màn hình 6 — Trả Truyện (bổ sung)
┌──────────────────────────────────────────────────────────┐
│  Phiếu thuê: #PT0042   Khách: Nguyễn Văn An             │
│  Ngày thuê: 01/07/2025   Hạn trả: 05/07/2025            │
│  Ngày trả thực tế: 07/07/2025  →  Trễ: 2 ngày           │
├──────────────────────────────────────────────────────────┤
│  Tình trạng truyện: ○ Nguyên vẹn  ○ Hư hỏng  ○ Mất mát │
├──────────────────────────────────────────────────────────┤
│  Tiền cọc đã thu:          50,000đ                       │
│  Phí phạt trễ (2 ngày):    10,000đ                       │
│  Tiền hoàn khách:          40,000đ                       │
│                                                          │
│              [ Xác nhận trả truyện ]                    │
└──────────────────────────────────────────────────────────┘
Mô tả: Màn hình xử lý trả truyện. Hệ thống tự tính số ngày trễ, phí phạt và số tiền cọc hoàn lại. Nhân viên chọn tình trạng truyện trước khi xác nhận.
```

```bash
5. Sơ Đồ Use Case
Các Actor
ActorMô tảAdminQuản trị viên — toàn quyền hệ thốngStaffNhân viên bán hàng — thao tác giao dịch hàng ngàyKhách hàngNgười mua / thuê truyện (tương tác gián tiếp qua Staff)
Danh sách Use Case chính
Actor: Admin
├── UC01 - Đăng nhập hệ thống
├── UC02 - Quản lý tài khoản nhân viên
├── UC03 - Xem báo cáo doanh thu
├── UC04 - Cấu hình quy định thuê / phạt
└── UC05 - Xem audit log

Actor: Staff
├── UC01 - Đăng nhập hệ thống
├── UC06 - Thêm / sửa / tìm kiếm truyện
├── UC07 - Tạo đơn bán hàng & thanh toán
├── UC08 - Tạo phiếu cho thuê
├── UC09 - Xử lý trả truyện & tính phạt
├── UC10 - Thêm / tra cứu khách hàng
└── UC11 - Xem lịch sử giao dịch khách hàng

6. Công Nghệ Sử Dụng
Thành phầnCông nghệNgôn ngữ lập trìnhPython 3.xGiao diện (Frontend)Tkinter / PyQt5 (QTDesigner)Cơ sở dữ liệuSQLite (hoặc MySQL)Thiết kế mockupCanva / Draw.ioQuản lý mã nguồnGit & GitHub

7. Cấu Trúc Thư Mục
```text
QuanLyCuaHangTruyen/
│
├── docs/
│   ├── URD_QuanLyCuaHangTruyen.pdf   # Tài liệu đặc tả yêu cầu
│   ├── mockups/                       # Hình ảnh thiết kế giao diện
│   │   ├── 01_Login.png
│   │   ├── 02_Dashboard.png
│   │   ├── 03_KhoTruyen.png
│   │   ├── 04_BanHang_ChoThue.png
│   │   ├── 05_KhachHang.png
│   │   └── 06_TraTruyen.png
│   └── diagrams/
│       ├── ERD.png                    # Sơ đồ thực thể quan hệ
│       └── UseCase.png                # Sơ đồ use case
│
├── src/
│   ├── main.py                        # Điểm khởi chạy ứng dụng
│   ├── ui/                            # Các file giao diện (.ui / .py)
│   ├── models/                        # Lớp dữ liệu (Model)
│   ├── controllers/                   # Xử lý logic nghiệp vụ
│   └── database/                      # Kết nối & migration CSDL
│
├── README.md
└── requirements.txt
```

```bash
8. Tài Liệu Đính Kèm Tuần 1
FileMô tảdocs/URD_QuanLyCuaHangTruyen.pdfTài liệu đặc tả yêu cầu chi tiếtdocs/mockups/*.pngHình ảnh thiết kế giao diện (6 màn hình)docs/diagrams/ERD.pngSơ đồ thực thể quan hệdocs/diagrams/UseCase.pngSơ đồ use case


📅 Tuần 1 — Hoàn thành: Mô tả chức năng & Phác thảo giao diện
📅 Tuần 2 — Tiếp theo: Xây dựng Frontend bằng Tkinter / QTDesigner
📅 Tuần 3 — Tiếp theo: Thiết kế Backend, Database & tích hợp hoàn chỉnh
```