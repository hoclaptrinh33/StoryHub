# Phase 7 Gate Report (Internal)

## Gate decision

- Result: PASS (with follow-up items)
- Date: 2026-04-19
- Scope: Integration tests + hardening cho API v1, POS checkout, Rental return

## Automated checks

### Backend contract and integration tests

- Command:
  - `Set-Location backend; e:/lehai/Documents/Project/StoryHub/.venv/Scripts/python.exe -m pytest`
- Result: PASS
- Detail: `60 passed in 10.29s`

### Frontend type and unit tests

- Command:
  - `Set-Location frontend; npm run type-check`
  - `Set-Location frontend; npm run test:run`
- Result: PASS
- Detail: `2 files, 5 tests passed`

### Hardening gate (lint/format)

- Command:
  - `Set-Location backend; e:/lehai/Documents/Project/StoryHub/.venv/Scripts/python.exe -m ruff check .`
  - `Set-Location backend; e:/lehai/Documents/Project/StoryHub/.venv/Scripts/python.exe -m ruff format --check .`
- Result: FAIL (non-blocking for Phase 7 functional gate)
- Detail:
  - Violation nhóm `I001`, `F401`, `E501` tập trung ở `app/api/v1/endpoints/checkout.py` và một phần `app/api/v1/endpoints/inventory.py`.
  - Đây là tồn đọng style, không làm fail các test nghiệp vụ đã chạy.

## Manual smoke run (POS + Rental return)

### Runtime used

- Backend: task `StoryHub: Backend Dev` tại `http://127.0.0.1:8000`
- Frontend: task `StoryHub: Frontend Dev` tại `http://127.0.0.1:5173`

### Smoke scenarios and outcomes

1. POS checkout success

- Route: `/ban-hang`
- Steps:
  - Nhập mã `9784088826001`
  - Thêm vào giỏ
  - Bấm `XUẤT HÓA ĐƠN`
- Result: PASS
- Evidence: Toast `Thanh toán thành công. Đơn mua #1003. Tổng thu: 30.000 ₫.`

2. Rental return settlement success

- Route: `/hoan-tra`
- Steps:
  - Chọn hợp đồng `#2001` từ danh sách `Hợp đồng đang thuê`
  - Quét item trả `ITM-CON98-001` qua scanner event
  - Bấm `Xác nhận & Kết toán`
- Result: PASS
- Evidence:
  - Toast `Kết toán thành công hợp đồng #2001. Hoàn khách 65.000 ₫.`
  - Toast `Settlement đã được cập nhật realtime cho HĐ #2001.`

3. Realtime and role/subscription baseline

- WebSocket endpoint: `/ws/item-live-updates?token=cashier-demo&branch_id=main`
- Result: PASS (sau khi bảo đảm backend đúng workspace đang chạy)
- Evidence: backend log `WebSocket ... [accepted]` và UI nhận sự kiện settlement realtime.

## Hardening findings and triage

### Major follow-up

1. Backend lint debt còn khá lớn ở một số endpoint (không ảnh hưởng pass/fail test runtime).

- Severity: Major
- Owner: Backend
- Plan: mở PR riêng chuẩn hóa import, bỏ unused imports, tách dòng dài theo `line-length=100`.

2. Manual keyboard typing không mô phỏng đúng scanner ở màn return trong test browser.

- Severity: Major
- Owner: Frontend QA/Automation
- Plan: trong automation dùng `storyhub:scan` event hoặc script scanner harness thay vì `keyboard.type` thông thường.

### Operational note

- Đã phát hiện một backend process cũ chiếm cổng `8000`, gây nhiễu smoke ban đầu (403/405 giả).
- Đã xử lý bằng cách dừng process cũ và chạy lại đúng task backend workspace.

## Phase 7 acceptance summary

- Full API contract/integration tests: PASS
- POS checkout smoke: PASS
- Rental return smoke: PASS
- Realtime settlement update smoke: PASS
- Blocker/Critical đang mở: Không phát hiện trong phạm vi gate này

## Suggested next actions before UAT

1. Dọn lint debt backend thành một PR riêng để đóng hardening style gate.
2. Chạy bug bash nội bộ tập trung keyboard-first và scanner edge cases.
3. Đóng gói release candidate cho Phase 8 kèm checklist UAT theo vai trò.
