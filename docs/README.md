# StoryHub Docs README

## 1) Giới thiệu dự án

StoryHub là hệ thống quản lý bán và cho thuê truyện theo mô hình desktop kiosk, tối ưu cho vận hành tại cửa hàng.

Định hướng chính của dự án:

- Local-first, offline-first để vẫn vận hành khi mạng không ổn định.
- Tập trung vào thao tác nhanh cho nhân viên quầy (keyboard-first, barcode-first).
- Dữ liệu giao dịch có khả năng truy vết với audit log, idempotency, và locking.

## 2) Bộ docs này dùng để làm gì

Thư mục docs là nguồn tham chiếu trung tâm cho toàn team:

- PM dùng để chốt phạm vi và lộ trình triển khai.
- Backend dùng để implement API, dữ liệu, và business rules.
- Frontend dùng để implement UI contract, user flow, trạng thái màn hình.
- QA dùng để xây test plan, test case và tiêu chí nghiệm thu.

Mục tiêu là giảm hiểu sai giữa các vai trò, đảm bảo mọi người cùng bám một hợp đồng tài liệu.

## 3) Tech stack

| Lớp hệ thống     | Công nghệ                   | Mục đích                                           |
| ---------------- | --------------------------- | -------------------------------------------------- |
| Frontend desktop | Vue 3 + Tauri               | Giao diện kiosk cho vận hành tại quầy              |
| Backend service  | FastAPI                     | Xử lý nghiệp vụ và cung cấp API nội bộ             |
| ORM              | SQLAlchemy                  | Truy cập dữ liệu theo mô hình đối tượng            |
| Database         | SQLite (lộ trình SQLCipher) | Lưu trữ local, dễ triển khai tại cửa hàng          |
| Realtime         | WebSocket                   | Đồng bộ trạng thái item và settlement gần realtime |
| Tài liệu API     | Markdown + YAML blueprint   | Mô tả hợp đồng API để implement và kiểm thử        |

## 4) Bắt đầu đọc từ đâu

Thứ tự đọc khuyến nghị cho thành viên mới:

1. [Tổng quan hệ thống](overview.md)
2. [Từ điển thuật ngữ chuẩn](standards/standard_terminology-glossary.md)
3. [Quy ước coding và workflow cộng tác](standards/standard_coding-and-collaboration.md)
4. [Thiết lập môi trường phát triển](how-to/howto_development-environment-setup.md)
5. [Lộ trình triển khai chi tiết](how-to/howto_project-implementation-steps.md)
6. Domain và lifecycle:
   - [Domain Item](domain/domain_item.md)
   - [Domain Rental Contract](domain/domain_rental-contract.md)
   - [Lifecycle Item](lifecycle/lifecycle_item.md)
   - [Lifecycle Rental Contract](lifecycle/lifecycle_rental-contract.md)
7. API blueprint tại [api-reference/v1](api-reference/v1)
8. UI contract và user flow:
   - [UI POS Main Kiosk](ui-contracts/ui_pos-main-kiosk.md)
   - [UI Rental Return Inspection](ui-contracts/ui_rental-return-inspection.md)
   - [Flow POS Checkout](user-flows/flow_pos-checkout.md)
   - [Flow Rental Return](user-flows/flow_rental-return.md)
9. Realtime, migration, config:
   - [Realtime contract](realtime/realtime_item-live-updates.yaml)
   - [Realtime implementation](realtime/implementation_websocket.md)
   - [Migration runbook](migrations/migration_blueprint-to-implementation-v1.md)
   - [Runtime config](config/config_storyhub-runtime.yaml)
10. [Lịch sử thay đổi phát hành](../CHANGELOG.md)

## 5) Giới thiệu chi tiết từng nhóm file docs

### 5.1) File định hướng chung

- [overview.md](overview.md): Bức tranh tổng thể về nghiệp vụ, kiến trúc, ràng buộc quan trọng.
- [\_registry.yaml](_registry.yaml): Chỉ mục máy đọc của toàn bộ docs, dùng cho kiểm tra coverage và điều hướng tooling.

### 5.2) API blueprint

- Thư mục: [api-reference/v1](api-reference/v1)
- Mỗi API có cặp file:
  - File .md để đọc nghiệp vụ và luồng xử lý.
  - File .yaml để định nghĩa hợp đồng kỹ thuật (input, output, error, auth, testing).
- Mục tiêu: Backend implement đúng contract, Frontend và QA kiểm thử nhất quán.

### 5.3) Domain, lifecycle, event, dataflow

- [domain](domain): Mô hình thực thể, quy tắc bất biến.
- [lifecycle](lifecycle): Vòng đời trạng thái của item và rental contract.
- [events](events): Sự kiện nghiệp vụ phát ra và consumer liên quan.
- [domain/dataflow_rental-return-settlement.md](domain/dataflow_rental-return-settlement.md): Luồng dữ liệu nghiệp vụ trả truyện và kết toán.

### 5.4) UI contract và user flow

- [ui-contracts](ui-contracts): Hợp đồng trạng thái màn hình và hành vi UI.
- [user-flows](user-flows): Luồng thao tác thực tế của người dùng vận hành.

### 5.5) Nền tảng kỹ thuật và vận hành

- [business-logic](business-logic): Quy tắc nghiệp vụ trọng yếu (locking, audit, barcode buffer).
- [database](database): Thiết kế schema cốt lõi.
- [config](config): Cấu hình runtime chuẩn.
- [realtime](realtime): Hợp đồng kênh realtime.
- [realtime/implementation_websocket.md](realtime/implementation_websocket.md): Chi tiết kiến trúc và lifecycle realtime.
- [migrations](migrations): Runbook chuyển từ blueprint sang implemented.
- [how-to](how-to): Hướng dẫn thực thi dự án theo giai đoạn.

### 5.6) Chuẩn phát triển và phát hành

- [standards/standard_terminology-glossary.md](standards/standard_terminology-glossary.md): Bộ thuật ngữ chuẩn để đồng bộ cách gọi giữa các vai trò.
- [standards/standard_coding-and-collaboration.md](standards/standard_coding-and-collaboration.md): Quy ước coding, review, commit và cộng tác.
- [how-to/howto_development-environment-setup.md](how-to/howto_development-environment-setup.md): Hướng dẫn setup môi trường dev cho thành viên mới.
- [how-to/runbook_websocket-troubleshooting.md](how-to/runbook_websocket-troubleshooting.md): Runbook debug realtime websocket.
- [../CHANGELOG.md](../CHANGELOG.md): Lịch sử thay đổi theo từng phiên bản phát hành.

## 6) Trạng thái tài liệu hiện tại

- Docs đang ở mode blueprint/design-first.
- API hiện mô tả hợp đồng cần triển khai, chưa mặc định là implemented.
- Khi code đã có và đã verify, cập nhật trạng thái tương ứng trong file docs và registry.

## 7) Quy tắc cập nhật docs

1. Mỗi thay đổi nghiệp vụ phải cập nhật ít nhất một trong các nhóm: API, domain/lifecycle, UI flow.
2. Nếu đổi contract API, cập nhật đồng thời cả .md và .yaml của endpoint đó.
3. Nếu thêm module mới, bổ sung link trong [overview.md](overview.md) và index trong [\_registry.yaml](_registry.yaml).
4. Với thay đổi có ảnh hưởng lớn, cập nhật thêm runbook trong [migrations](migrations).

## 8) Checklist đọc nhanh trước khi triển khai

- [ ] Đã đọc [overview.md](overview.md)
- [ ] Đã đọc [standards/standard_terminology-glossary.md](standards/standard_terminology-glossary.md)
- [ ] Đã đọc [standards/standard_coding-and-collaboration.md](standards/standard_coding-and-collaboration.md)
- [ ] Đã chạy [how-to/howto_development-environment-setup.md](how-to/howto_development-environment-setup.md)
- [ ] Đã đọc [how-to/howto_project-implementation-steps.md](how-to/howto_project-implementation-steps.md)
- [ ] Đã xác nhận API cần làm trong [api-reference/v1](api-reference/v1)
- [ ] Đã đối chiếu UI contract và user flow tương ứng
- [ ] Đã xem constraint kỹ thuật trong [business-logic](business-logic)
