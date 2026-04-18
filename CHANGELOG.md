# Changelog

Tài liệu này theo dõi lịch sử thay đổi theo từng phiên bản phát hành của StoryHub.

Định dạng tham chiếu: Keep a Changelog và Semantic Versioning.

## [Unreleased]

### Phase 4: Triển khai UI Kiosk & Trải nghiệm Người dùng
- **Added**: Triển khai **Unified Checkout System**: Giao diện bàn thu ngân "Fast Checkout" UX, hỗ trợ giỏ hàng hỗn hợp (bán và thuê).
- **Added**: Triển khai **Zero Friction CRM**: Tích hợp tìm kiếm và tạo khách hàng ngầm định trực tiếp tại đơn thuê, loại bỏ Modal cồng kềnh.
- **Added**: Hệ thống **Global Barcode Listener**: Nhận diện barcode toàn cục, phân biệt scanner và nhập tay bằng buffer timeout.
- **Added**: Bộ **Keyboard Shortcuts (F1, Enter, Esc)**: Tối ưu hóa thao tác không cần chuột cho nhân viên vận hành.
- **Added**: Màn hình **Rental Return Inspection**: Quy trình kiểm tra trả truyện theo đúng state machine nghiệp vụ.
- **Added**: Tài liệu hướng dẫn chi tiết tại `docs/how-to/howto_phase4-keyboard-shortcuts.md`.

### Phase 3: Triển khai API Cốt lõi & Logic Nghiệp vụ
- **Added**: API **Inventory Management**: Logic giữ chỗ (reserve), khóa (lock) và giải phóng item tự động.
- **Added**: API **Unified Checkout**: Endpoint `POST /checkout/unified` xử lý thanh toán đa năng.
- **Added**: API **Rental & Settlement**: Tính toán phí thuê, tiền cọc, tiền phạt và hoàn cọc tự động.
- **Added**: API **CRM**: Quản lý khách hàng với tính năng upsert nhanh.
- **Added**: Cơ chế **Idempotency**: Đảm bảo an toàn giao dịch khi replay request.
- **Added**: Hệ thống **Audit Logs**: Ghi lại lịch sử thay đổi (before/after) cho các tác vụ quan trọng.
- **Added**: Tài liệu logic nghiệp vụ tại `docs/business-logic/unified-checkout-and-inventory.md`.

### Phase 2: Dữ liệu & Schema Cốt lõi
- **Added**: Cấu trúc Database StoryHub Core: Lớp dữ liệu Title, Volume, Item và Transaction.
- **Added**: Hệ thống **Migration Runner**: Hỗ trợ up/down/status cho SQLite.
- **Added**: Script **Idempotent Seeding**: Dữ liệu mẫu phong phú cho POS, Rental và báo cáo.
- **Added**: Cơ chế **Soft Delete** và Audit Columns cho các bảng nghiệp vụ chính.
- **Added**: Thiết lập Index và Ràng buộc (Constraints) bảo vệ toàn vẹn dữ liệu.

### Phase 1: Dựng Khung Kỹ thuật (Skeleton)
- **Added**: Backend Skeleton: FastAPI project structure, Health check, Response Envelope chuẩn v1.
- **Added**: Frontend Skeleton: Vue 3 + Vite + Tauri desktop shell, Layout Kiosk 3 cột.
- **Added**: Bộ script setup tự động: `scripts/setup.ps1` (install, migrate, seed).
- **Added**: Cấu hình kiểm tra chất lượng: Lint, Format (Ruff/Eslint), Type-check (TS).
- **Added**: Hệ thống Logging cơ bản cho cả Backend và Frontend.

### Changed
- Tái cấu trúc Router Frontend: Hợp nhất các màn hình cũ (`sale.vue`, `rentalorder.vue`) thành màn hình Checkout thống nhất.
- Cập nhật `system fuction.md` để đồng bộ với kiến trúc Unified POS mới.

### Removed
- Loại bỏ các View cũ lỗi thời: `order-sale.vue`, `rentalorder.vue`, `sale.vue`.

## [0.1.0] - 2026-04-14

### Added

- Khởi tạo backend skeleton ban đầu (FastAPI).
- Khởi tạo frontend Vue 3 ban đầu.
- Khởi tạo Tauri desktop shell.
- Bổ sung script dev cơ bản.
- Bổ sung cấu hình VS Code.

### Changed

- Cập nhật tài liệu gốc để phản ánh trạng thái đã setup được môi trường chạy local.
