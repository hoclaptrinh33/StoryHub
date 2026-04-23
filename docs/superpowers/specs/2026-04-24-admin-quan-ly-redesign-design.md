# StoryHub Admin `/quan-ly` Redesign - Design Spec

- Date: 2026-04-24
- Status: Draft for review
- Scope: Full-stack redesign trang quản lý theo mô hình 1 route + 5 tab lớn
- Decision owner: Product Owner (map `admin = owner`)

## 1. Bối cảnh

Trang `/quan-ly` hiện có UI và logic chưa đồng bộ:

- UI chưa khớp layout tab ngang như định hướng mới.
- File frontend đang monolithic, có nhiều đoạn placeholder và gọi sai API.
- Nhiều API admin đã có ở backend nhưng chưa được nối đúng token/flow.
- Một số năng lực nghiệp vụ còn thiếu endpoint chuyên biệt (đặc biệt emergency refund cho rental rollback full).

Mục tiêu của bản redesign là chuẩn hóa một trung tâm quản trị duy nhất cho owner, vừa giám sát vừa thao tác đặc quyền với độ an toàn và audit rõ ràng.

## 2. Mục tiêu và không mục tiêu

### 2.1. Mục tiêu

1. Giữ **1 route duy nhất**: `/quan-ly`.
2. Dùng **tab ngang 5 nhóm lớn**:
   - Data & Audit
   - Promotions
   - HR & RBAC
   - Pricing
   - System & Backup
3. Layout nội dung theo lựa chọn đã duyệt: **Option B** (split panel cố định trái/phải).
4. Chỉ `owner` truy cập toàn bộ (map yêu cầu `admin = owner`).
5. Hoàn thiện full-stack: frontend + endpoint thiếu + audit + test.

### 2.2. Không mục tiêu

1. Không tách thành nhiều route con cho từng tab.
2. Không tạo role mới `admin` trong DB/JWT ở phase này.
3. Không đổi luồng nghiệp vụ POS/Rental ngoài phần cần tích hợp admin.
4. Không thêm bước duyệt 2 lớp cho bulk pricing (đã chốt 1-step apply).

## 3. Quyết định đã chốt

1. Phương án kỹ thuật: **PA2** (1 route, tách tab thành component/composable).
2. Layout tổng thể: **B** (tab ngang + split panel cố định).
3. Quyền truy cập: chỉ `owner`; map `admin = owner`.
4. Emergency refund: áp dụng cho cả `sale` và `rental`.
5. Emergency refund rental: **rollback toàn bộ hợp đồng**.
6. Guard thao tác nguy hiểm: chỉ bắt buộc nhập `reason`, không cần xác nhận lần 2 bằng chuỗi.
7. Bulk pricing update: **owner bấm áp dụng chạy ngay** (1 bước).

## 4. Kiến trúc UI/UX

## 4.1. Khung trang

Trang `/quan-ly` gồm 4 lớp:

1. Header hệ thống hiện tại (giữ nguyên để đồng bộ toàn app).
2. Hero admin (tiêu đề, badge quyền, KPI theo tab).
3. Tab strip ngang 5 nhóm nghiệp vụ.
4. Content split:
   - Panel trái cố định (filters, actions, warnings).
   - Panel phải động theo tab (table/form/timeline).

## 4.2. Responsive

1. Desktop: split 2 cột cố định (`~320px` trái, còn lại phải).
2. Tablet/mobile:
   - Tab strip scroll ngang.
   - Panel trái chuyển thành khối collapsible/drawer.
   - Panel phải full width.

## 4.3. Nguyên tắc tương tác

1. Tất cả thao tác ghi dữ liệu đều có trạng thái loading + disabled button.
2. Tất cả thao tác nguy hiểm yêu cầu lý do (`reason`) trước khi submit.
3. Sau thao tác thành công: reload dữ liệu liên quan + cập nhật audit list.
4. Toast chỉ để phản hồi ngắn; chi tiết lỗi đọc từ response envelope.

## 5. Kiến trúc frontend (PA2)

## 5.1. Cấu trúc thành phần

- `views/manager.vue`
  - Admin shell + tab strip + split layout
  - Điều phối state chung, token, refresh orchestration
- `components/admin/tabs/DataAuditTab.vue`
- `components/admin/tabs/PromotionsTab.vue`
- `components/admin/tabs/HrRbacTab.vue`
- `components/admin/tabs/PricingTab.vue`
- `components/admin/tabs/SystemTab.vue`
- `composables/useAdminApi.ts`
  - Wrapper gọi `storyhubApi` với token từ auth store

## 5.2. State chuẩn hóa

1. `activeTab`: tab hiện tại.
2. `dashboardKpis`: số liệu nhanh theo tab.
3. `loadingMap`: loading độc lập theo action/key.
4. `errorMap`: lỗi theo vùng UI.
5. `modalState`: override/refund/hard-delete/user/voucher/pricing.

## 5.3. Auth & token flow

1. Đọc token từ `useAuthStore().token`.
2. Nếu không có token hoặc role khác `owner`: redirect về route phù hợp.
3. Toàn bộ admin API gửi `Authorization: Bearer <real token>`.
4. Không dùng default demo token cho luồng admin.

## 6. Ma trận chức năng theo tab

## 6.1. Tab Data & Audit

### 6.1.1. CRM Admin

- Danh sách toàn bộ khách: `GET /api/v1/customers/all`
- Override công nợ/cọc/blacklist: `PATCH /api/v1/customers/{id}/admin-override`
- UI yêu cầu reason bắt buộc.

### 6.1.2. Transaction monitoring

- Danh sách giao dịch: `GET /api/v1/system/transactions`
- Hard delete: `POST /api/v1/system/transactions/{transaction_type}/{reference_id}/hard-delete`
- Emergency refund sale: `POST /api/v1/system/transactions/sale/{order_id}/emergency-refund`
- **Emergency refund rental (mới)**:
  - `POST /api/v1/system/transactions/rental/{contract_id}/emergency-refund`

### 6.1.3. Audit log

- Danh sách audit: `GET /api/v1/system/audit-logs`
- Cho phép lọc tối thiểu theo `action`, `entity_type`, phân trang.

## 6.2. Tab Promotions

### 6.2.1. Voucher

- List: `GET /api/v1/promotions/vouchers`
- Create: `POST /api/v1/promotions/vouchers`
- Update/toggle: `PATCH /api/v1/promotions/vouchers/{id}`
- Delete: `DELETE /api/v1/promotions/vouchers/{id}`

### 6.2.2. Automatic promotion

- List: `GET /api/v1/promotions/auto-promotions`
- Create: `POST /api/v1/promotions/auto-promotions`
- Toggle: `PATCH /api/v1/promotions/auto-promotions/{id}/toggle`
- Delete: `DELETE /api/v1/promotions/auto-promotions/{id}`
- **Update full thông tin (mới)**:
  - `PATCH /api/v1/promotions/auto-promotions/{id}`
  - Cho phép sửa `name`, `day_of_week`, `discount_percent`, `is_active`

### 6.2.3. Tự động giảm giá ngày Thứ 3

Bổ sung áp dụng vào luồng checkout unified:

- Khi tạo giao dịch thuê, backend kiểm tra `automatic_promotion` active theo ngày hiện tại.
- Nếu có rule hợp lệ, giảm phần rental theo `%` rule.
- Lưu dấu vết áp dụng vào order/rental snapshots và audit.

## 6.3. Tab HR & RBAC

- List user: `GET /api/v1/system/users`
- Create user: `POST /api/v1/system/users`
- Update user: `PATCH /api/v1/system/users/{id}`
  - Đổi role (`cashier`/`manager`)
  - Đổi mật khẩu
  - Khóa/mở tài khoản

Ràng buộc:

1. Owner không tự khóa/chỉnh chính mình qua API admin update.
2. Không cho chỉnh tài khoản owner khác.

## 6.4. Tab Pricing

- Active pricing rule: `GET /api/v1/system/pricing/active`
- Update active rule: `PATCH /api/v1/system/pricing/active`
- Bulk update giá: `POST /api/v1/system/pricing/bulk-update` (1-step)

Thông số hiển thị/chỉnh:

- `k_rent`
- `k_deposit`
- `d_floor`
- `used_demand_factor`
- `used_cap_ratio`
- `note`

## 6.5. Tab System & Backup

- Config cửa hàng: `GET/PATCH /api/v1/system/config`
  - `shop_name`
  - `shop_address`
  - `shop_phone`
  - `bill_footer`
  - `penalty_per_day`
- Backup:
  - Trigger: `POST /api/v1/system/backups`
  - Latest: `GET /api/v1/system/backups/latest`

## 7. Backend bổ sung/chỉnh sửa

## 7.1. Endpoint mới: emergency refund rental

### 7.1.1. API contract

- Method: `POST`
- Path: `/api/v1/system/transactions/rental/{contract_id}/emergency-refund`
- Auth: `owner` + scope `admin:write`
- Request body:
  - `reason` (required, min length 3)
  - `request_id` (required, idempotency)
  - `refund_method` (`cash|bank_transfer|e_wallet|original_method`, default `original_method`)

### 7.1.2. Hành vi nghiệp vụ

1. Validate contract tồn tại, chưa bị delete, trạng thái cho phép refund.
2. Tính tổng tiền hoàn từ dữ liệu hợp đồng thuê (rental fee + deposit thực thu, trừ phần đã settle nếu cần theo rule hiện tại).
3. Rollback toàn bộ item trong contract:
   - `item.status` về `available`
   - xóa/thu hồi liên kết rental item
4. Cập nhật hợp đồng sang trạng thái `cancelled` hoặc `refunded` (khuyến nghị dùng `cancelled` để tương thích enum hiện tại).
5. Ghi bản ghi refund rental vào bảng riêng.
6. Ghi audit log với before/after đầy đủ và reason.

### 7.1.3. Schema bổ sung

Thêm migration mới tạo:

1. `rental_refund`
   - `id`
   - `contract_id`
   - `reason`
   - `refund_method`
   - `refunded_total`
   - `request_id` (unique)
   - `created_by_user_id`
   - `created_at`
2. `rental_refund_item`
   - `id`
   - `refund_id`
   - `rental_item_id`
   - `item_id`
   - `amount`

Ghi chú: tương tự pattern `pos_refund`/`pos_refund_item` để đảm bảo nhất quán.

## 7.2. Endpoint mới: update automatic promotion

- Method: `PATCH`
- Path: `/api/v1/promotions/auto-promotions/{promo_id}`
- Body: `name?`, `day_of_week?`, `discount_percent?`, `is_active?`
- Yêu cầu ít nhất 1 field thay đổi.
- Ghi `AUTO_PROMO_UPDATED` vào audit.

## 7.3. Tích hợp auto promotion vào checkout

Chỉnh `checkout.unified`:

1. Resolve auto promo active theo ngày.
2. Chỉ áp dụng vào phần rental subtotal theo rule đã bật.
3. Không vượt quá subtotal rental.
4. Ghi vào `order_item` snapshot/audit:
   - promo id
   - promo name
   - discount amount

## 8. Audit log chuẩn hóa hành động

Bổ sung/chuẩn hóa action codes:

1. `ADMIN_CUSTOMER_OVERRIDE`
2. `TRANSACTION_HARD_DELETED`
3. `POS_ORDER_EMERGENCY_REFUNDED`
4. `RENTAL_CONTRACT_EMERGENCY_REFUNDED` (mới)
5. `VOUCHER_CREATED|UPDATED|DELETED`
6. `AUTO_PROMO_CREATED|UPDATED|ACTIVATED|DEACTIVATED|DELETED`
7. `USER_CREATED|USER_UPDATED`
8. `PRICE_RULE_UPDATED`
9. `PRICING_BULK_UPDATE_APPLIED`
10. `SYSTEM_CONFIG_UPDATED`
11. `SYSTEM_BACKUP_CREATED`

Mỗi log phải lưu:

- `actor_user_id`
- `entity_type`, `entity_id`
- `before_json`, `after_json`
- `ip_address`, `device_id`
- timestamp

## 9. Error handling

## 9.1. Backend

1. Giữ format `ResponseEnvelope` chuẩn.
2. Dùng mã lỗi nghiệp vụ rõ ràng (`*_NOT_FOUND`, `*_INVALID`, `*_CONFLICT`).
3. Transactional integrity cho hard-delete/refund/bulk-update.
4. Idempotency cho emergency refund endpoints.

## 9.2. Frontend

1. Parse `StoryHubApiError` để show message backend.
2. Với lỗi validation, highlight field tại modal/form.
3. Với lỗi conflict, giữ nguyên modal để user chỉnh và submit lại.

## 10. Test strategy

## 10.1. Backend tests

1. Unit/integration cho endpoint mới `rental emergency refund`:
   - success rollback full
   - contract not found
   - contract already refunded/cancelled
   - idempotent replay by `request_id`
2. Test `PATCH auto-promotion`:
   - update từng field
   - reject payload rỗng
3. Test auto-promo apply trong `checkout.unified`:
   - đúng ngày có giảm
   - không đúng ngày không giảm
   - không vượt subtotal
4. Regression test cho endpoints admin cũ còn hoạt động.

## 10.2. Frontend tests

1. Render/regression cho shell `/quan-ly` + 5 tabs.
2. Tab switching không mất state filter nội bộ tab khi phù hợp.
3. Modal reason validation cho action nguy hiểm.
4. API error mapping ra UI đúng thông điệp.

## 11. Kế hoạch triển khai đề xuất (tầng kỹ thuật)

1. Refactor frontend `manager.vue` thành shell + tab components.
2. Sửa `storyhubApi.ts` mapping hàm admin và token usage.
3. Bổ sung backend endpoint `rental emergency refund` + migration refund tables.
4. Bổ sung backend endpoint update auto-promotion.
5. Tích hợp auto-promo vào checkout unified.
6. Viết test backend + frontend trọng yếu.
7. Smoke test end-to-end role owner tại `/quan-ly`.

## 12. Tiêu chí nghiệm thu

1. Owner vào `/quan-ly` thấy đủ 5 tab, layout B đúng thiết kế.
2. Mọi chức năng trong yêu cầu đều thao tác được bằng API thực, không còn placeholder.
3. Emergency refund hoạt động cho cả sale và rental; rental rollback full.
4. Mọi thao tác nguy hiểm bắt buộc reason, được ghi audit.
5. Bulk pricing update chạy 1 bước và có audit sample changes.
6. Backup tạo được file artifact và xem được trạng thái latest.

## 13. Rủi ro và kiểm soát

1. Rủi ro sai lệch dữ liệu khi refund rental rollback.
   - Kiểm soát: transaction + test rollback + audit chi tiết.
2. Rủi ro xung đột với code đang chỉnh dở trong repo.
   - Kiểm soát: chỉ chạm module/admin files trong phase triển khai.
3. Rủi ro coupling trong file API service frontend.
   - Kiểm soát: gom admin API vào nhóm wrapper/composable riêng.

## 14. Kết luận

Thiết kế này bám đúng quyết định đã duyệt:

- 1 trang `/quan-ly`
- 5 tab lớn
- layout B
- owner-only (admin map owner)
- emergency refund cho sale + rental rollback full
- thao tác nguy hiểm chỉ cần reason
- pricing bulk update 1 bước

Thiết kế sẵn sàng chuyển sang bước lập implementation plan.
