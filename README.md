# StoryHub

StoryHub là hệ thống quản lý bán và cho thuê truyện theo mô hình desktop kiosk, tối ưu cho vận hành tại cửa hàng.

Mục tiêu chính:

- Local-first và offline-first để hệ thống vẫn vận hành khi mạng không ổn định.
- Keyboard-first và barcode-first để thao tác nhanh tại quầy.
- Dữ liệu giao dịch có khả năng truy vết qua audit log, idempotency và locking.

## 1) Kiến trúc tổng quan

| Lớp hệ thống     | Công nghệ                   | Vai trò                                            |
| ---------------- | --------------------------- | -------------------------------------------------- |
| Frontend desktop | Vue 3 + Tauri               | Giao diện kiosk cho nhân viên vận hành             |
| Backend service  | FastAPI                     | Xử lý nghiệp vụ và cung cấp API nội bộ             |
| ORM              | SQLAlchemy                  | Truy cập dữ liệu theo mô hình đối tượng            |
| Database         | SQLite (lộ trình SQLCipher) | Lưu trữ local tại cửa hàng                         |
| Realtime         | WebSocket                   | Đồng bộ trạng thái item và settlement gần realtime |

## 2) Cấu trúc repository

```text
StoryHub/
├─ backend/        # FastAPI service (API, config, DB session, test)
├─ frontend/       # Vue 3 + Vite + Tauri desktop shell
├─ docs/           # Blueprint và tài liệu nghiệp vụ/kỹ thuật
├─ scripts/        # Script setup/chạy dev cho Windows PowerShell
├─ CHANGELOG.md    # Lịch sử thay đổi theo phiên bản
└─ README.md       # Tổng quan dự án
```

## 3) Yêu cầu hệ thống

- Python 3.13+
- Node.js 20+
- Rust toolchain (`rustup`, `rustc`, `cargo`)
- Visual Studio Build Tools (C++) cho Windows để build Tauri
- WebView2 Runtime

Kiểm tra nhanh:

```powershell
python --version
node --version
npm --version
rustc --version
cargo --version
```

## 4) Thiết lập môi trường phát triển

Tại thư mục gốc dự án:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

Script setup sẽ:

- Tạo/cập nhật môi trường Python `.venv`.
- Cài dependency backend trong `backend/`.
- Cài dependency frontend trong `frontend/`.
- Tạo `.env` từ `.env.example` nếu chưa có.

## 5) Chạy hệ thống ở môi trường local

### 5.1) Chạy backend

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-backend.ps1
```

- URL mặc định: `http://127.0.0.1:8000`
- Health endpoint: `GET /api/v1/health`

### 5.2) Chạy frontend web

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-frontend.ps1
```

- URL mặc định: `http://127.0.0.1:5173`

### 5.3) Chạy desktop app với Tauri

```powershell
cd frontend
npm run tauri:dev
```

Build desktop app:

```powershell
cd frontend
npm run tauri:build
```

Nếu gặp lỗi thiếu C++ toolchain khi build, hãy cài Visual Studio Build Tools và chạy lại.

## 6) Bộ tài liệu quan trọng

- Tổng quan docs: [docs/README.md](docs/README.md)
- Tổng quan hệ thống: [docs/overview.md](docs/overview.md)
- Hướng dẫn setup cho developer mới: [docs/how-to/howto_development-environment-setup.md](docs/how-to/howto_development-environment-setup.md)
- Lộ trình triển khai theo giai đoạn: [docs/how-to/howto_project-implementation-steps.md](docs/how-to/howto_project-implementation-steps.md)
- API blueprint v1: [docs/api-reference/v1](docs/api-reference/v1)
- Chuẩn thuật ngữ: [docs/standards/standard_terminology-glossary.md](docs/standards/standard_terminology-glossary.md)
- Quy ước coding và cộng tác: [docs/standards/standard_coding-and-collaboration.md](docs/standards/standard_coding-and-collaboration.md)
- Lịch sử thay đổi phát hành: [CHANGELOG.md](CHANGELOG.md)

## 7) Workflow cộng tác đề xuất

1. Đọc tài liệu liên quan trong `docs/` trước khi code.
2. Tạo branch theo mục đích (`feature/*`, `fix/*`, `hotfix/*`).
3. Triển khai thay đổi nhỏ, đúng phạm vi ticket.
4. Chạy test/lint cần thiết trước khi tạo pull request.
5. Cập nhật docs và changelog khi thay đổi ảnh hưởng hành vi hệ thống.

## 8) Trạng thái hiện tại

- Dự án đang theo mô hình design-first: docs blueprint đã đầy đủ để triển khai.
- Backend và frontend đã có skeleton chạy local.
- Tauri desktop shell đã được khởi tạo trong `frontend/src-tauri`.

## 9) Changelog

Theo dõi lịch sử phát hành tại [CHANGELOG.md](CHANGELOG.md).
