# How-to: Thiết lập môi trường phát triển cho developer mới

> Loại tài liệu: How-to Guide
> Đối tượng: Developer mới tham gia dự án
> Mục tiêu: Chạy được backend, frontend và desktop shell trên máy local

## 1) Điều kiện tiên quyết

Cài đặt sẵn các công cụ sau:

- Python 3.13+
- Node.js 20+
- Rust toolchain (rustup, rustc, cargo)
- Build Tools C++ cho Windows (MSVC) để build Tauri
- WebView2 Runtime

Kiểm tra nhanh bằng lệnh:

```powershell
python --version
node --version
npm --version
rustc --version
cargo --version
```

## 2) Lấy mã nguồn

```powershell
git clone https://github.com/hoclaptrinh33/StoryHub
cd StoryHub
```

## 3) Setup dependency toàn dự án

Tại thư mục gốc project:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

Script này sẽ:

- Tạo/cập nhật Python virtual environment tại `.venv`.
- Cài dependency backend trong `backend/`.
- Cài dependency frontend trong `frontend/`.
- Tạo file `.env` từ `.env.example` nếu chưa có.

## 4) Chạy backend

Mở terminal 1:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-backend.ps1
```

Kiểm tra health endpoint:

- `GET http://127.0.0.1:8000/api/v1/health`

## 5) Chạy frontend web

Mở terminal 2:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-frontend.ps1
```

Frontend mặc định chạy tại:

- `http://127.0.0.1:5173`

## 6) Chạy desktop app (Tauri)

Mở terminal 3:

```powershell
cd frontend
npm run tauri:dev
```

Build desktop app:

```powershell
cd frontend
npm run tauri:build
```

## 7) Kiểm tra nhanh sau khi setup

- Backend trả `status: ok` ở health endpoint.
- Frontend mở được trang chính và bấm nút kiểm tra backend không lỗi.
- Tauri boot thành công, mở cửa sổ desktop app.

## 8) Sự cố thường gặp

### 8.1) `cargo` không được nhận diện trong terminal

Nguyên nhân: terminal chưa nhận PATH mới sau khi cài Rust.

Cách xử lý:

- Đóng và mở lại terminal, hoặc
- Chạy tạm trong phiên hiện tại:

```powershell
$env:Path = "$env:USERPROFILE\\.cargo\\bin;$env:Path"
```

### 8.2) Lỗi thiếu C++ build tools khi chạy Tauri

Nguyên nhân: chưa cài MSVC Build Tools.

Cách xử lý:

- Cài Visual Studio Build Tools với workload C++.
- Chạy lại `npm run tauri:dev`.

### 8.3) Lỗi Execution Policy khi chạy script PowerShell

Cách xử lý:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
```

## 9) Tài liệu liên quan

- [Runtime config](../config/config_storyhub-runtime.yaml)
- [Lộ trình triển khai](./howto_project-implementation-steps.md)
- [Quy ước coding và cộng tác](../standards/standard_coding-and-collaboration.md)
