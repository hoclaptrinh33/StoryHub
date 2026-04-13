# Quy ước coding và workflow cộng tác StoryHub

> Loại tài liệu: Engineering Standard
> Trạng thái: active
> Phiên bản: 1.0.0

## 1) Mục tiêu

Tài liệu này thống nhất cách viết code, review và phối hợp giữa các thành viên để giảm lỗi tích hợp và tăng tốc độ release.

## 2) Quy ước coding

### 2.1) Quy ước chung

- Ưu tiên thay đổi nhỏ, đúng phạm vi ticket.
- Tên rõ nghĩa, tránh viết tắt khó hiểu.
- Không commit code tạm: debug log, commented-out code, hardcoded test value.
- Mọi logic có side effects phải có xử lý lỗi và thông điệp lỗi rõ ràng.

### 2.2) Backend (FastAPI)

- Tách lớp theo trách nhiệm: API router, service logic, data access.
- Endpoint trả status code nhất quán theo API blueprint.
- Endpoint có side effects phải hỗ trợ idempotency.
- Vi phạm business rule trả lỗi có mã lỗi ổn định để frontend map được.
- Quy ước naming Python:
  - module/file: `snake_case`
  - class: `PascalCase`
  - function/variable: `snake_case`
  - constant: `UPPER_SNAKE_CASE`

### 2.3) Frontend (Vue 3 + Tauri)

- Component ưu tiên theo feature, tránh component đa nhiệm quá lớn.
- Trạng thái loading/error/success phải hiển thị rõ ràng cho thao tác vận hành.
- Luồng POS và Rental Return ưu tiên keyboard-first.
- Copy hiển thị cho người vận hành dùng tiếng Việt đầy đủ dấu.
- Quy ước naming frontend:
  - component: `PascalCase.vue`
  - composable: `useXxx.ts`
  - utility: `camelCase.ts`

### 2.4) Logging, bảo mật và hiệu năng

- Log phải có `request_id` hoặc trace context khi xử lý giao dịch.
- Không log dữ liệu nhạy cảm (token, thông tin định danh đầy đủ).
- Validate input ở API boundary; không tin dữ liệu từ client.
- Truy vấn nóng phải có index tương ứng theo schema docs.

## 3) Workflow cộng tác

### 3.1) Branching

- `main`: nhánh ổn định để phát hành.
- `feature/<module>-<short-name>`: tính năng mới.
- `fix/<module>-<short-name>`: sửa lỗi.
- `hotfix/<module>-<short-name>`: sửa lỗi khẩn cấp trên bản phát hành.

Ví dụ:

- `feature/rental-return-fee-calculation`
- `fix/pos-idempotency-replay`

### 3.2) Commit message

Dùng format:

`type(scope): summary`

Ví dụ:

- `feat(rental): add return settlement calculator`
- `fix(pos): prevent duplicate order on replay request`
- `docs(standards): add terminology glossary`

### 3.3) Pull request

PR cần có:

- Mô tả mục tiêu thay đổi.
- Danh sách file/chức năng bị ảnh hưởng.
- Ảnh chụp hoặc video ngắn nếu thay đổi UI.
- Checklist test đã chạy.
- Rủi ro và kế hoạch rollback (nếu có).

### 3.4) Review và merge

- Ít nhất 1 reviewer bắt buộc cho thay đổi nhỏ.
- Ít nhất 2 reviewer cho thay đổi liên quan dữ liệu tài chính hoặc workflow rental.
- Chỉ merge khi CI xanh và không còn comment blocker.
- Ưu tiên squash merge để lịch sử gọn và dễ truy vết.

## 4) Definition of Done (DoD)

Một ticket được xem là hoàn tất khi thỏa đồng thời:

- Code đã chạy được trên môi trường dev.
- Test tối thiểu cho phần thay đổi đã pass.
- Docs liên quan đã cập nhật (API/domain/UI flow nếu bị ảnh hưởng).
- Không còn blocker/critical issue mở trong PR.

## 5) Trách nhiệm cập nhật tài liệu

Khi thay đổi nghiệp vụ hoặc contract:

- Cập nhật docs blueprint liên quan trong `docs/`.
- Nếu có thay đổi phát hành, cập nhật `CHANGELOG.md`.
- Nếu thêm thuật ngữ mới, cập nhật glossary chuẩn.
