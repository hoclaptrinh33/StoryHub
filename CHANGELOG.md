# Changelog

Tài liệu này theo dõi lịch sử thay đổi theo từng phiên bản phát hành của StoryHub.

Định dạng tham chiếu: Keep a Changelog và Semantic Versioning.

## [Unreleased]

### Added

- Bổ sung tài liệu chuẩn thuật ngữ tại `docs/standards/standard_terminology-glossary.md`.
- Bổ sung tài liệu quy ước coding và workflow cộng tác tại `docs/standards/standard_coding-and-collaboration.md`.
- Bổ sung hướng dẫn setup môi trường dev cho developer mới tại `docs/how-to/howto_development-environment-setup.md`.

## [0.1.0] - 2026-04-14

### Added

- Khởi tạo backend skeleton với FastAPI, cấu hình runtime, health endpoint và test smoke.
- Khởi tạo frontend Vue 3 + TypeScript + Vite cho StoryHub.
- Khởi tạo Tauri desktop shell trong `frontend/src-tauri`.
- Bổ sung script setup/chạy dev tại `scripts/setup.ps1`, `scripts/dev-backend.ps1`, `scripts/dev-frontend.ps1`.
- Bổ sung cấu hình VS Code tasks và extension recommendations.

### Changed

- Cập nhật tài liệu gốc để phản ánh trạng thái đã setup được môi trường chạy local.
