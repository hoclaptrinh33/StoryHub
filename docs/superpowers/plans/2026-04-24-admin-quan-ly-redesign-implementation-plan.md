# StoryHub Admin `/quan-ly` Redesign - Implementation Plan

- Date: 2026-04-24
- Input spec: `docs/superpowers/specs/2026-04-24-admin-quan-ly-redesign-design.md`
- Scope: Full-stack implementation theo thiết kế đã duyệt (PA2, layout B, owner-only)

## 1. Mục tiêu triển khai

1. Hoàn thiện trang `/quan-ly` theo mô hình 1 route + 5 tab lớn với split panel cố định (layout B).
2. Đảm bảo tất cả tính năng admin hoạt động bằng API thật, không còn placeholder.
3. Bổ sung backend endpoint còn thiếu:
   - Emergency refund cho rental (rollback full contract).
   - Update đầy đủ auto-promotion.
4. Đồng bộ frontend token flow (`owner` token thực) cho toàn bộ admin calls.
5. Có test regression cho luồng quan trọng và audit log đầy đủ.

## 2. Nguyên tắc thực thi

1. Chỉ `owner` được truy cập và thao tác toàn bộ `/quan-ly` (map `admin = owner`).
2. Mọi thao tác nguy hiểm phải có `reason` bắt buộc.
3. Thay đổi DB phải đi qua migration mới, không chỉnh tay schema runtime trong production path.
4. Mỗi phase có tiêu chí done rõ ràng trước khi sang phase sau.
5. Ưu tiên giữ tương thích với dữ liệu và endpoint hiện có để giảm regression.

## 3. Phân rã phase

## Phase 0 - Baseline & Alignment

### Mục tiêu

Chốt baseline code để triển khai an toàn trong worktree đang có thay đổi.

### Công việc

1. Chụp snapshot trạng thái hiện tại của các file liên quan admin (frontend/backend).
2. Xác nhận module đích cần chỉnh trong vòng này:
   - `frontend/src/views/manager.vue` và các component/composable admin mới.
   - `frontend/src/services/storyhubApi.ts` (nhóm admin API).
   - `backend/app/api/v1/endpoints/system.py`, `promotions.py`, `checkout.py`.
   - migration mới cho refund rental.
3. Xác định test hiện hữu chạy được để làm baseline regression.

### Done

- Có danh sách file chạm chính thức cho vòng triển khai.
- Không chỉnh ngoài phạm vi đã chốt.

---

## Phase 1 - Backend: API & Data Foundation

### Mục tiêu

Bổ sung đầy đủ backend capability để frontend admin gọi ổn định.

### Công việc

1. Migration mới cho refund rental:
   - Tạo `rental_refund`.
   - Tạo `rental_refund_item`.
   - Index/constraint cần thiết (`request_id` unique, FK hợp lệ).
2. `system.py`:
   - Thêm `POST /system/transactions/rental/{contract_id}/emergency-refund`.
   - Transaction logic rollback full contract:
     - restore `item.status = available`.
     - xử lý `rental_item`, `rental_settlement`, `rental_contract` theo rule đã chốt.
     - ghi `rental_refund` + `rental_refund_item`.
     - ghi audit `RENTAL_CONTRACT_EMERGENCY_REFUNDED`.
3. `promotions.py`:
   - Thêm `PATCH /promotions/auto-promotions/{promo_id}` để update full fields.
   - Validation payload rỗng và giới hạn giá trị.
   - Ghi audit `AUTO_PROMO_UPDATED`.
4. `checkout.py`:
   - Tích hợp auto-promotion active theo ngày vào phần rental.
   - Đảm bảo giảm giá không vượt subtotal rental.
   - Ghi audit/snapshot trường áp dụng promo.
5. Kiểm tra tương thích endpoint cũ:
   - sale emergency refund
   - hard delete sale/rental
   - users/config/pricing/backups.

### Done

- Endpoint mới chạy được bằng test/API manual.
- Migration apply/revert sạch trên DB local test.
- Không phá endpoint admin hiện có.

---

## Phase 2 - Frontend: Admin Shell Refactor (PA2)

### Mục tiêu

Đưa `/quan-ly` về kiến trúc tab-based maintainable, đồng bộ UI theo layout B.

### Công việc

1. Refactor `manager.vue` thành shell:
   - Hero + tab ngang 5 nhóm.
   - Split panel trái/phải.
   - routing guard owner-only.
2. Tách logic theo tab vào component/composable:
   - `DataAuditTab`
   - `PromotionsTab`
   - `HrRbacTab`
   - `PricingTab`
   - `SystemTab`
3. Chuẩn hóa API calls:
   - Dùng đúng tên hàm service hiện có (`fetchAdminTransactions`, `hardDeleteAdminTransaction`, ...).
   - Truyền `authStore.token` cho toàn bộ admin API.
4. Hoàn thiện modal thao tác:
   - CRM override
   - hard delete
   - emergency refund (sale + rental)
   - create/update voucher, auto-promo
   - create/update user
   - pricing update + bulk price
5. Hoàn thiện loading/error/toast states theo action key.
6. Responsive behavior:
   - desktop split cố định.
   - mobile: panel trái collapsible/drawer.

### Done

- `/quan-ly` render ổn định với 5 tab, không còn nút placeholder “đang phát triển”.
- Tất cả thao tác chính gọi API thật và phản hồi đúng.

---

## Phase 3 - Integration Hardening

### Mục tiêu

Đảm bảo tính nhất quán nghiệp vụ giữa backend và UI.

### Công việc

1. Đồng bộ type TS trong `storyhubApi.ts` cho endpoint mới.
2. Chuẩn hóa mapping mã lỗi backend -> thông điệp UI.
3. Kiểm tra lại permission failure (`403`) hiển thị rõ ở UI admin.
4. Đảm bảo mọi action nguy hiểm bắt buộc nhập `reason` trước submit.
5. Kiểm tra audit list phản ánh thao tác vừa thực hiện (refresh sau action).

### Done

- Không còn mismatch payload giữa frontend và backend.
- UI xử lý được lỗi validation/conflict/network hợp lý.

---

## Phase 4 - Test & Quality Gate

### Mục tiêu

Khóa chất lượng trước khi bàn giao.

### Công việc

1. Backend tests mới:
   - rental emergency refund success + rollback full.
   - rental emergency refund edge cases (not found, state invalid, idempotent replay).
   - patch auto-promotion update fields.
   - checkout unified with auto-promo by day.
2. Frontend tests:
   - manager shell render + tab switch.
   - modal reason validation cho thao tác nguy hiểm.
   - API error presentation.
3. Regression smoke:
   - login owner -> `/quan-ly`.
   - data/audit actions.
   - pricing bulk update 1-step.
   - backup trigger + latest status.

### Done

- Test suite mục tiêu pass.
- Smoke checklist pass.

---

## Phase 5 - Rollout & Handover

### Mục tiêu

Bàn giao an toàn cho vận hành.

### Công việc

1. Ghi release notes cho module admin redesign.
2. Cập nhật tài liệu API nếu endpoint mới thay đổi contract.
3. Chuẩn bị rollback note:
   - rollback migration mới nếu cần.
   - disable UI action tương ứng bằng feature guard tạm thời.
4. Chốt checklist vận hành tại cửa hàng:
   - backup manual chạy được.
   - quyền owner hoạt động đúng.

### Done

- Có tài liệu sử dụng và rollback cơ bản.
- Chủ shop có thể vận hành độc lập các chức năng mới.

## 4. Ma trận phụ thuộc

1. Phase 1 phải xong trước khi khóa Phase 2 (do frontend cần endpoint mới).
2. Phase 2 và Phase 3 có thể đan xen một phần, nhưng merge theo thứ tự backend-first.
3. Phase 4 chỉ bắt đầu khi Phase 1-3 hoàn tất.
4. Phase 5 thực hiện sau quality gate pass.

## 5. File touch plan (dự kiến)

### Backend

1. `backend/app/api/v1/endpoints/system.py`
2. `backend/app/api/v1/endpoints/promotions.py`
3. `backend/app/api/v1/endpoints/checkout.py`
4. `backend/app/db/migrations/0006_*.up.sql`
5. `backend/app/db/migrations/0006_*.down.sql`
6. `backend/tests/test_*` liên quan admin/refund/promotion

### Frontend

1. `frontend/src/views/manager.vue`
2. `frontend/src/components/admin/tabs/*.vue` (mới)
3. `frontend/src/composables/useAdminApi.ts` (mới)
4. `frontend/src/services/storyhubApi.ts`
5. `frontend/src/router/index.ts` (nếu cần guard refinement)
6. `frontend/src/__tests__/*` cho manager/admin

## 6. Definition of Done (DoD)

1. Owner truy cập `/quan-ly` đầy đủ 5 tab theo layout B.
2. CRM override, hard delete, emergency refund (sale + rental rollback full) hoạt động thật.
3. Voucher + auto-promotion CRUD đủ create/update/delete/toggle.
4. Auto promotion áp dụng tự động vào checkout rental theo ngày.
5. HR actions (create user, đổi pass, khóa/mở, đổi role) hoạt động.
6. Pricing update + bulk update 1 bước hoạt động và có audit.
7. System config + backup hoạt động.
8. Tất cả thao tác nguy hiểm yêu cầu reason và có audit trail.
9. Test + smoke checklist đạt.

## 7. Kế hoạch thực thi ngắn hạn (execution order)

1. Phase 1 (backend) - triển khai endpoint/migration thiếu.
2. Phase 2 (frontend shell + tabs).
3. Phase 3 (integration hardening).
4. Phase 4 (test gate).
5. Phase 5 (rollout docs).

## 8. Rủi ro chính và giảm thiểu

1. Dữ liệu rental rollback sai lệch.
   - Giảm thiểu: transaction toàn khối + test scenario đầy đủ.
2. Worktree đang nhiều thay đổi song song.
   - Giảm thiểu: giới hạn file touch đúng module, commit nhỏ theo phase.
3. API contract drift giữa frontend/backend.
   - Giảm thiểu: chốt types ở `storyhubApi.ts` trước khi hoàn thiện UI.
