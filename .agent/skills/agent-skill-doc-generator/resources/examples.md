# Examples — Ví dụ đầy đủ và Prompt mẫu

> File này chứa full examples cho Agent tham khảo khi sinh docs,
> cùng với danh sách prompt mẫu cho user.

---

## 1. Full Example — File `.yaml` (getUserData)

```yaml
# ============================================================
# PHẦN 1: IDENTITY — Định danh tool
# ============================================================
name: getUserData
description: "Lấy thông tin chi tiết của user theo ID. Trả về object chứa name, email, age, role. Chỉ trả về user đang active."
version: 1.2.0
deprecated: false
tags: ["user-management", "database", "read-only"]
category: "core/user"
priority: high

# Liên kết đến file doc dành cho Dev (cùng thư mục)
doc_ref: "api_get-user-data_v1.md"

# ============================================================
# PHẦN 1b: HTTP ENDPOINT — Thông tin API route
# ============================================================
http:
  method: GET
  path: "/api/v1/users/:user_id"
  path_params:
    user_id:
      type: string
      format: uuid
  query_params: {}
  request_body: null
  content_type: "application/json"

# ============================================================
# PHẦN 2: PARAMETERS — Tham số đầu vào
# ============================================================
parameters:
  type: object
  required: [user_id]
  properties:
    user_id:
      type: string
      description: "UUID v4 định danh user duy nhất trong hệ thống"
      format: uuid
      constraints:
        pattern: "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
      examples: ["550e8400-e29b-41d4-a716-446655440000"]
    include_deleted:
      type: boolean
      description: "Bao gồm cả user đã soft-delete"
      default: false
      required: false

# ============================================================
# PHẦN 3: RETURNS — Giá trị trả về
# ============================================================
returns:
  type: object
  properties:
    id:
      type: string
      format: uuid
    name:
      type: string
      description: "Họ tên đầy đủ"
    email:
      type: string
      format: email
    age:
      type: integer
      minimum: 0
      maximum: 200
    role:
      type: string
      enum: ["admin", "editor", "viewer"]
    created_at:
      type: string
      format: date-time

# ============================================================
# PHẦN 4: BEHAVIOR CONTRACT — Hợp đồng hành vi
# ============================================================
behavior:
  deterministic: true
  idempotent: true
  retryable: true
  side_effects: "read-only"
  latency: low
  cacheable: true

# ============================================================
# PHẦN 5: ERROR SCHEMA — Định nghĩa lỗi
# ============================================================
errors:
  - code: USER_NOT_FOUND
    type: NotFoundError
    http_status: 404
    description: "User ID không tồn tại hoặc đã bị xóa vĩnh viễn"
    retryable: false
    suggested_action: "Kiểm tra lại user_id, hoặc thử với include_deleted=true"
  - code: DB_CONNECTION_FAILED
    type: ConnectionError
    http_status: 503
    description: "Không thể kết nối đến database"
    retryable: true
    max_retries: 3
    retry_delay_ms: 1000
    suggested_action: "Retry sau 1 giây, tối đa 3 lần"
  - code: INVALID_UUID
    type: ValidationError
    http_status: 400
    description: "user_id không đúng format UUID v4"
    retryable: false
    suggested_action: "Kiểm tra format UUID, phải là UUID v4"

# ============================================================
# PHẦN 6: AUTH CONTEXT — Xác thực & phân quyền
# ============================================================
auth:
  required: true
  type: "Bearer Token"
  roles: ["admin", "editor", "self"]
  scopes: ["read:users"]
  notes: "Role 'self' chỉ cho phép xem thông tin của chính mình"

# ============================================================
# PHẦN 7: TOOL DEPENDENCIES — Phụ thuộc giữa các tool
# ============================================================
dependencies:
  requires: ["authenticate"]
  provides: ["user_context"]
  conflicts_with: ["deleteUser"]
  optional: ["getUserPermissions"]

# ============================================================
# PHẦN 8: RATE LIMITING — Giới hạn tần suất
# ============================================================
rate_limit:
  max_calls_per_minute: 120
  max_concurrent: 10
  cooldown_ms: 0
  burst_limit: 20

# ============================================================
# PHẦN 9: PERFORMANCE — Hiệu năng
# ============================================================
performance:
  expected_latency_ms: 150
  timeout_ms: 5000
  cache_ttl_seconds: 300

# ============================================================
# PHẦN 10: ENVIRONMENT — Môi trường chạy
# ============================================================
environment:
  supported: ["production", "staging", "development"]
  requires_services: ["postgres", "redis"]
  runtime: "Node.js >= 18"

# ============================================================
# PHẦN 11: STRUCTURED EXAMPLES — Ví dụ có cấu trúc
# ============================================================
examples:
  - name: "Happy path — Lấy user thành công"
    input:
      user_id: "550e8400-e29b-41d4-a716-446655440000"
    output:
      id: "550e8400-e29b-41d4-a716-446655440000"
      name: "Nguyễn Văn A"
      email: "nguyenvana@example.com"
      age: 28
      role: "editor"
      created_at: "2024-01-15T08:30:00Z"
  - name: "Edge case — User không tồn tại"
    input:
      user_id: "00000000-0000-4000-8000-000000000000"
    error:
      code: USER_NOT_FOUND
      message: "User not found"
  - name: "Edge case — UUID không hợp lệ"
    input:
      user_id: "not-a-uuid"
    error:
      code: INVALID_UUID
      message: "Invalid UUID format"

# ============================================================
# PHẦN 12: VERSIONING — Quản lý phiên bản
# ============================================================
versioning:
  backward_compatible: true
  changelog:
    - version: 1.2.0
      date: "2024-03-15"
      changes: "Thêm field 'role' vào response"
    - version: 1.1.0
      date: "2024-02-01"
      changes: "Thêm parameter 'include_deleted'"
    - version: 1.0.0
      date: "2024-01-01"
      changes: "Initial release"
  migration_hint: "Từ v1.1 lên v1.2: response thêm field 'role', không breaking change"

# ============================================================
# PHẦN 13: OBSERVABILITY — Quan sát & giám sát
# ============================================================
observability:
  logging_level: info
  metrics: ["call_count", "latency_p50", "latency_p99", "error_rate"]
  trace_propagation: true
  alert_on: ["error_rate > 5%", "latency_p99 > 3000ms"]

# ============================================================
# PHẦN 14: SOURCE TRACKING — Theo dõi nguồn gốc
# ============================================================
source_tracking:
  files:
    - path: "src/services/user.service.ts"
      hash: "sha256:a1b2c3d4e5f6..."
    - path: "src/models/user.model.ts"
      hash: "sha256:f6e5d4c3b2a1..."
  generated_at: "2024-03-15T10:30:00Z"
  generator_version: "agent-skill-doc-generator@1.0"
```

### Giải thích các phần trong file `.yaml`

| Phần | Mục đích | Bắt buộc? |
|---|---|---|
| **Identity** | Agent biết tool này là gì, tìm kiếm theo tags | ✅ Bắt buộc |
| **HTTP Endpoint** | Agent biết gọi API ở đâu, method gì, path gì | ✅ Bắt buộc (cho API) |
| **doc_ref** | Liên kết đến file `.md` tương ứng (cho cross-reference) | ✅ Bắt buộc |
| **Parameters** | Agent biết truyền gì vào | ✅ Bắt buộc |
| **Returns** | Agent biết nhận gì ra | ✅ Bắt buộc |
| **Behavior Contract** | Agent biết retry/parallel/cache được không | ✅ Bắt buộc |
| **Error Schema** | Agent biết xử lý lỗi thế nào | ✅ Bắt buộc |
| **Auth Context** | Agent biết có quyền gọi không | ✅ Bắt buộc |
| **Tool Dependencies** | Agent biết gọi theo thứ tự nào | ⚠️ Nên có |
| **Rate Limiting** | Agent biết giới hạn tần suất | ⚠️ Nên có |
| **Performance** | Agent set timeout hợp lý | ⚠️ Nên có |
| **Environment** | Agent biết chạy ở đâu | 🟡 Optional |
| **Structured Examples** | Agent self-validate output | ⚠️ Nên có |
| **Versioning** | Quản lý evolution, changelog | ⚠️ Nên có |
| **Observability** | Debug production | 🟡 Optional |
| **Source Tracking** | Phát hiện doc outdated, incremental update | ⚠️ Nên có |

---

## 2. Full Example — File `.md` (getUserData)

```markdown
# getUserData

> **Schema file:** [`api_get-user-data_v1.yaml`](./api_get-user-data_v1.yaml)
> **Version:** 1.2.0 | **Category:** core/user | **Priority:** High

## Mô tả chức năng

> **WHY**: Endpoint cơ bản nhất trong user management. Mọi tính năng hiển thị profile,
> phân quyền, và personalization đều phụ thuộc vào function này.

Lấy thông tin chi tiết của một user dựa trên UUID. Chỉ trả về user đang active,
trừ khi `include_deleted=true`.

## Tham số

| Tên | Kiểu | Bắt buộc | Mô tả |
|-----|------|----------|-------|
| `user_id` | `string (UUID v4)` | ✅ | ID duy nhất của user |
| `include_deleted` | `boolean` | ❌ | Bao gồm user đã soft-delete. Default: `false` |

## Ví dụ sử dụng

### Cơ bản
```typescript
const user = await getUserData({ user_id: "550e8400-..." });
console.log(user.name); // "Nguyễn Văn A"
```

### Với include_deleted
```typescript
const user = await getUserData({
  user_id: "550e8400-...",
  include_deleted: true
});
```

## Response Schema

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Nguyễn Văn A",
  "email": "nguyenvana@example.com",
  "age": 28,
  "role": "editor",
  "created_at": "2024-01-15T08:30:00Z"
}
```

## Edge Cases

| Case | Input | Kết quả |
|------|-------|---------|
| User không tồn tại | UUID hợp lệ nhưng không có trong DB | `USER_NOT_FOUND` (404) |
| UUID sai format | `"not-a-uuid"` | `INVALID_UUID` (400) |
| User đã soft-delete | UUID user đã xóa, `include_deleted=false` | `USER_NOT_FOUND` (404) |
| Database timeout | Bất kỳ | `DB_CONNECTION_FAILED` (503), retryable |

## Lưu ý hiệu năng

- Response được cache trong Redis với TTL 5 phút
- Cache key: `user:{user_id}`
- Cache tự invalidate khi user update profile
- Expected latency: ~150ms

## Lưu ý bảo mật

- Yêu cầu Bearer Token hợp lệ
- Role `self` chỉ cho phép xem chính mình (so sánh token.sub với user_id)
- Không trả về fields nhạy cảm: `password_hash`, `two_factor_secret`
- Rate limited: 120 calls/phút/user

## Changelog

| Version | Ngày | Thay đổi |
|---------|------|----------|
| 1.2.0 | 2024-03-15 | Thêm field `role` vào response |
| 1.1.0 | 2024-02-01 | Thêm parameter `include_deleted` |
| 1.0.0 | 2024-01-01 | Initial release |
```

### Điểm khác biệt giữa `.yaml` và `.md`

| Tiêu chí | File `.yaml` | File `.md` |
|---|---|---|
| **Agent load** | Load trực tiếp, parse YAML | Không cần load |
| **Dev đọc** | Khó đọc cho người | Đọc ngay, rõ ràng |
| **Validate** | YAML schema validator | Markdown linter |
| **CI/CD** | `find . -name "*.yaml"` | Markdown check tools |
| **Cross-reference** | `doc_ref` trỏ sang `.md` | Link trỏ sang `.yaml` |

---

## 3. Prompt mẫu gọi skill

### Sinh docs — để skill tự chọn tier
```
"Sinh docs cho toàn bộ API trong src/controllers/, mode detailed"
```
→ Agent tự quét project signals → chọn tier → tạo cấu trúc phù hợp → sinh files

### Sinh docs — chỉ định tier cụ thể
```
"Sinh docs cho project này, dùng Tier 2 (Standard), mode summary"
```
→ Agent dùng Tier 2 bất kể project signals

### Sinh docs cho 1 API endpoint (Tier bất kỳ)
```
"Sinh docs cho function getUserData trong file src/services/user.service.ts, mode detailed"
```
→ Kết quả: `api_get-user-data_v1.md` + `api_get-user-data_v1.yaml`

### Sinh docs cho cả module
```
"Sinh docs cho toàn bộ module user-service, mode summary"
```
→ Kết quả: Nhiều cặp `.md` + `.yaml` cho mỗi function

### Chỉ sinh schema cho agent (không cần .md)
```
"Sinh schema-only cho tất cả API endpoints trong src/controllers/"
```
→ Kết quả: Chỉ các file `.yaml` rút gọn

### Sinh docs cho webhook
```
"Sinh docs cho webhook payment-success, mode detailed"
```
→ Kết quả: `wh_payment-success.md` + `wh_payment-success.yaml`

### Khởi tạo cấu trúc docs cho dự án mới
```
"Khởi tạo cấu trúc thư mục docs/ cho dự án này"
```
→ Agent quét project → chọn tier → tạo cấu trúc phù hợp (KHÔNG tạo thư mục trống)

### Upgrade docs hiện có
```
"Upgrade docs hiện có trong docs/ thành dual-output format mới, tách thành .yaml và .md riêng biệt"
```
→ Kết quả: Tách file cũ thành cặp `.yaml` + `.md`, restructure theo tier phù hợp

### Sinh docs cho business logic (chỉ .md, không cần .yaml)
```
"Sinh docs cho logic phân quyền trong src/auth/"
```
→ Kết quả: `logic_role-permissions.md`

### Nâng tier khi dự án phát triển
```
"Dự án đã thêm 15 endpoints mới, restructure docs/ cho phù hợp"
```
→ Agent tính lại signals → đề xuất nâng tier → tạo migration plan → hỏi user confirm

---

## 4. Prompt mẫu — Blueprint Mode (Design-First)

### Sinh docs từ ý tưởng đơn giản
```
"Tớ muốn thiết kế API quản lý giỏ hàng: thêm sản phẩm, xóa sản phẩm, tính tổng tiền.
Dùng blueprint mode, tạo docs cho các endpoint này."
```
→ Agent sinh cặp `bp_cart-add-item_v1.yaml/md`, `bp_cart-remove-item_v1.yaml/md`, `bp_cart-calculate-total_v1.yaml/md`

### Sinh docs từ user stories
```
"User stories:
- Là người bán, tôi muốn tạo sản phẩm mới với tên, giá, hình ảnh
- Là người mua, tôi muốn tìm kiếm sản phẩm theo tên
- Là admin, tôi muốn xem báo cáo doanh thu theo ngày
Hãy sinh blueprint docs cho toàn bộ."
```
→ Agent phân tích stories → sinh IR giả định → sinh blueprint docs cho từng endpoint

### Chuyển blueprint thành docs thật (sau khi đã code)
```
"Code cho cart module đã implement xong tại src/services/cart.service.ts.
Hãy chuyển blueprint docs thành docs thật từ source code."
```
→ Agent đọc code thật → so sánh với blueprint → sinh docs mới (mode detailed) + đánh dấu blueprint là replaced

---

## 5. Prompt mẫu — Doc Types mới (v2.0)

### Domain Model — Sinh docs nghiệp vụ
```
"Sinh domain model cho entity User và Book trong hệ thống thư viện.
Bao gồm invariants, aggregates, relationships."
```
→ Agent sinh `domain_user.yaml/md`, `domain_book.yaml/md` với invariants, business rules

### Lifecycle / State Machine — Sinh vòng đời entity
```
"Entity Book có các trạng thái: available, reserved, borrowed, returned, archived.
Sinh lifecycle docs với transitions và guards."
```
→ Agent sinh `lifecycle_book.yaml/md` với states, transitions, auto-transitions

### Event System — Sinh docs sự kiện
```
"Sinh event docs cho event book_borrowed: khi user mượn sách thành công,
hệ thống cần update inventory, gửi email, đặt lịch nhắc."
```
→ Agent sinh `event_book-borrowed.yaml/md` với payload, consumers, delivery

### UI Contract — Sinh frontend spec
```
"Sinh UI contract cho trang User Profile. Component hiển thị thông tin user,
cho phép edit, có các state: loading, success, error, empty."
```
→ Agent sinh `ui_user-profile.yaml/md` với states, data_binding, interactions, error_handling

### User Flow — Sinh luồng thao tác
```
"Sinh user flow cho feature mượn sách: từ quét thẻ NFC → tìm sách → xác nhận mượn.
Bao gồm happy path, edge cases, error recovery."
```
→ Agent sinh `flow_borrow-book.md` với step-by-step, alternative paths, error recovery

### Configuration — Sinh config docs
```
"Sinh config docs cho module borrowing: max_books_per_user, borrow_duration_days,
overdue_penalty. Cần support multiple environments."
```
→ Agent sinh `config_borrowing.yaml` với values, defaults, env overrides

### Realtime / WebSocket — Sinh realtime docs
```
"Hệ thống có WebSocket channel để push realtime updates về trạng thái sách.
Sinh realtime docs cho channel library-updates."
```
→ Agent sinh `realtime_library-updates.yaml` với events, subscriptions, performance

### Full-stack — Sinh TẤT CẢ doc types
```
"Sinh docs toàn bộ cho hệ thống thư viện: domain, lifecycle, events, APIs,
UI contracts, user flows, config. Mode detailed, doc types all."
```
→ Agent quét project → sinh tất cả doc types phù hợp → tạo registry đầy đủ

### Contract Testing — Sinh test specs
```
"Thêm testing section vào api_get-user_v1.yaml: contract tests, mock data,
frontend test scenarios cho loading/error/empty states."
```
→ Agent bổ sung testing section vào file .yaml hiện có
