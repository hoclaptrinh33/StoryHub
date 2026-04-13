# Runtime & Execution — Behavior nâng cao, Failure Strategy, Configuration, Observability

> File này chứa templates và hướng dẫn nâng cấp cho:
> **Enhanced Behavior Contract**, **Failure Strategy**, **Configuration Layer**,
> **Enhanced Observability**, **Enhanced Permission Model (ABAC)**,
> **Enhanced Dependency Graph**, **Enhanced Tier Detection**.
> Tham chiếu từ `SKILL.md` chính.

---

## 1. Enhanced Behavior Contract — Hợp đồng hành vi nâng cao

### 1.1. Tại sao cần nâng cấp

Behavior contract hiện tại:
```yaml
behavior:
  deterministic: true
  retryable: true
```

👉 **Quá nông.** Agent vẫn phải "đoán":
- Khi nào được phép gọi API? (preconditions)
- Sau khi gọi xong, trạng thái hệ thống thay đổi thế nào? (postconditions)
- Nếu fail thì làm gì? (failure strategy)
- API này write vào đâu cụ thể? (side-effect scope)

### 1.2. Behavior Contract v2 — Template

```yaml
# Thay thế / mở rộng section behavior: trong api_*.yaml
behavior:
  # === GIỮ NGUYÊN TỪ V1 ===
  deterministic: true             # Cùng input → cùng output?
  idempotent: true                # Gọi nhiều lần → kết quả giống nhau?
  retryable: true                 # Có thể retry khi fail?
  side_effects: "database_write"  # none | read-only | database_write | external_call | mixed
  latency: low                   # low (<200ms) | medium (<1s) | high (<5s) | very_high (>5s)
  cacheable: false                # Response có thể cache?

  # === MỚI: PRECONDITIONS ===
  # Điều kiện PHẢI đúng TRƯỚC KHI gọi API
  # Agent phải verify preconditions → nếu false thì KHÔNG gọi API
  preconditions:
    - condition: ""               # Biểu thức boolean
      check_via: ""               # API/method để kiểm tra (nếu cần)
      error_if_false: ""          # Error code trả về nếu precondition fail
      # Ví dụ:
      # - condition: "user.status == 'active'"
      #   check_via: "api_get-user_v1"
      #   error_if_false: "USER_INACTIVE"

  # === MỚI: POSTCONDITIONS ===
  # Trạng thái hệ thống SAU KHI API chạy thành công
  # Agent dùng để verify kết quả và update internal state
  postconditions:
    - effect: ""                  # Thay đổi gì trong hệ thống
      verifiable: true            # Agent có thể verify bằng API khác không
      verify_via: ""              # API để verify (nếu verifiable)
      # Ví dụ:
      # - effect: "book.status = 'borrowed'"
      #   verifiable: true
      #   verify_via: "api_get-book_v1"

  # === MỚI: SIDE-EFFECT SCOPE CHI TIẾT ===
  # Agent biết chính xác API này đọc/ghi vào đâu
  side_effect_scope:
    reads: []                     # Danh sách resources đọc (tables, services...)
    writes: []                    # Danh sách resources ghi
    external: []                  # Danh sách external services gọi
    # Ví dụ:
    # reads: ["users", "books", "config"]
    # writes: ["transactions", "books"]
    # external: ["email_service", "notification_service"]

  # === MỚI: FAILURE STRATEGY ===
  # Cách xử lý khi gặp từng loại lỗi cụ thể
  # Agent PHẢI theo failure strategy này, KHÔNG được tự ý quyết định
  failure_strategy: {}
    # Ví dụ:
    # DB_CONNECTION_FAILED:
    #   action: retry              # retry | skip | fallback | abort | circuit_break
    #   max_retries: 3
    #   backoff: exponential       # fixed | linear | exponential
    #   backoff_base_ms: 1000
    #   fallback: cached_data      # Dùng gì khi hết retry
    #   alert: true                # Có gửi alert không
    # EMAIL_SERVICE_DOWN:
    #   action: skip
    #   fallback: queue_for_retry
    #   alert: false

  # === MỚI: FRONTEND BEHAVIOR HINTS ===
  # Gợi ý cho frontend biết cách hiển thị
  frontend:
    loading_strategy: ""          # skeleton | spinner | shimmer | progress_bar | none
    error_surface: ""             # toast | modal | inline | fullpage | snackbar
    empty_state: ""               # illustration | text_only | redirect | hide_section
    cache_strategy: ""            # none | cache-first | stale-while-revalidate | cache-only
    retry_ui: false               # true = hiện nút retry trên UI
    optimistic_updates: false     # true = update UI trước khi API response về
```

---

## 2. Enhanced Dependency Graph — Đồ thị phụ thuộc nâng cao

### 2.1. Tại sao cần nâng cấp

Dependency hiện tại:
```yaml
dependencies:
  requires: ["authenticate"]
```

👉 **Thiếu:**
- Thứ tự thực thi rõ ràng
- Conditional dependency (chỉ cần khi condition X)
- Fallback khi dependency fail
- Parallel vs sequential

### 2.2. Dependencies v2 — Template

```yaml
# Thay thế / mở rộng section dependencies: trong api_*.yaml
dependencies:
  # === REQUIRED — Bắt buộc, có thứ tự ===
  requires:
    - tool: ""                    # Tên tool/API cần gọi trước
      order: 1                   # Thứ tự thực thi (cùng order = chạy song song)
      mandatory: true             # true = phải thành công mới tiếp | false = best-effort
      provides_data: ""           # Data mà dependency này cung cấp cho API chính
      # Ví dụ:
      # - tool: authenticate
      #   order: 1
      #   mandatory: true
      #   provides_data: "auth_token, user_context"
      # - tool: check_user_status
      #   order: 2
      #   mandatory: true
      #   provides_data: "user.status, user.active_loans"
      # - tool: get_book_availability
      #   order: 2                # Cùng order 2 → chạy song song với check_user_status
      #   mandatory: true
      #   provides_data: "book.status, book.available_count"

  # === CONDITIONAL — Chỉ cần khi điều kiện đúng ===
  conditional:
    - tool: ""
      condition: ""               # Biểu thức boolean khi nào cần gọi
      # Ví dụ:
      # - tool: notify_admin
      #   condition: "book.category == 'rare' OR book.value > 1000"
      # - tool: check_parent_consent
      #   condition: "user.age < 18"

  # === FALLBACK — Thay thế khi dependency fail ===
  fallback:
    - tool: ""                    # Tool thay thế
      replaces: ""                # Tool bị thay thế
      when: ""                    # Điều kiện kích hoạt fallback
      degraded: true              # true = chức năng bị giảm khi dùng fallback
      # Ví dụ:
      # - tool: get_user_cached
      #   replaces: get_user
      #   when: "primary_db_unavailable"
      #   degraded: true

  # === PROVIDES — API này cung cấp gì cho tool khác ===
  provides: []                    # Danh sách data/context cung cấp

  # === CONFLICTS — Không chạy đồng thời ===
  conflicts_with: []              # Danh sách tools KHÔNG chạy song song với API này
  conflict_reason: ""             # Lý do conflict (ví dụ: "race condition trên cùng resource")
```

### 2.3. Quy tắc orchestration từ dependency graph

```
Agent đọc dependencies → xây execution plan:

1. Sort theo order → tạo execution stages
2. Cùng order → chạy song song (Promise.all)
3. Khác order → chạy tuần tự
4. mandatory: true → abort pipeline nếu fail
5. mandatory: false → skip, log warning
6. conditional → chỉ chạy khi condition == true
7. fallback → auto-switch khi primary fail
8. conflicts_with → lock resource, không chạy đồng thời
```

---

## 3. Enhanced Permission Model — ABAC (Attribute-Based Access Control)

### 3.1. Tại sao cần nâng cấp

Auth hiện tại:
```yaml
auth:
  roles: ["admin"]
```

👉 **Quá thô.** Thiếu:
- Conditional permission (user chỉ xem data của mình)
- Context-based (librarian chỉ quản lý chi nhánh mình)
- Frontend auth (ẩn/disable UI elements)

### 3.2. Auth v2 — Template

```yaml
# Thay thế / mở rộng section auth: trong api_*.yaml
auth:
  # === GIỮ NGUYÊN TỪ V1 ===
  required: true
  type: "Bearer Token"           # Bearer Token | API Key | OAuth2 | Basic
  scopes: []                     # OAuth2 scopes

  # === NÂNG CẤP: PERMISSION MODEL (ABAC) ===
  permissions:
    - role: ""                    # Tên role
      access: ""                  # full | conditional | read_only | deny
      condition: ""               # Biểu thức boolean (khi access = conditional)
      fields_allowed: []          # Danh sách fields được truy cập (nếu giới hạn)
      fields_denied: []           # Danh sách fields KHÔNG được truy cập
      # Ví dụ:
      # - role: admin
      #   access: full
      # - role: user
      #   access: conditional
      #   condition: "user.id == resource.owner_id"
      #   fields_denied: ["internal_notes", "admin_flags"]
      # - role: librarian
      #   access: conditional
      #   condition: "user.branch_id == resource.branch_id"

  # === MỚI: FRONTEND AUTH (UI enforcement) ===
  frontend_auth:
    hide_actions: []              # UI elements bị ẩn nếu không đủ quyền
    disable_actions: []           # UI elements bị disable nếu không đủ quyền
    route_guard:
      min_role: ""                # Role tối thiểu để truy cập trang
      redirect_to: ""             # Redirect nếu không đủ quyền
      show_message: ""            # Thông báo hiển thị

  # === MỚI: DATA FILTERING ===
  data_filtering:
    auto_filter: true             # true = tự động filter data theo quyền user
    filter_field: ""              # Field dùng để filter (ví dụ: "branch_id")
    # Ví dụ: librarian gọi GET /books → chỉ trả về sách thuộc branch của họ
```

---

## 4. Configuration Layer — Cấu hình Runtime

### 4.1. Khi nào tạo

- Có giá trị "magic number" trong business logic (max books, timeout days...)
- Giá trị cần thay đổi mà không sửa code
- Giá trị khác nhau giữa environments
- Nhiều API cùng reference 1 config value

### 4.2. Template `config_{module}.yaml`

```yaml
# File: config_{module}.yaml
# Cấu hình runtime cho module

# IDENTITY
config: ""                        # Tên module config (ví dụ: "borrowing")
description: ""                   # Mô tả module config
scope: ""                         # global | per-tenant | per-environment

# VALUES — Các giá trị cấu hình
values:
  key_name:
    type: ""                      # integer | string | boolean | number | array
    default: null                 # Giá trị mặc định
    description: ""               # Mô tả
    env_var: ""                   # Environment variable name (nếu có)
    min: null                     # Giá trị tối thiểu (cho number/integer)
    max: null                     # Giá trị tối đa
    options: []                   # Giá trị cho phép (enum)
    sensitive: false              # true = không log value
    hot_reload: false             # true = có thể thay đổi runtime không cần restart
    # Ví dụ:
    # max_books_per_user:
    #   type: integer
    #   default: 5
    #   description: "Số sách tối đa mỗi user được mượn cùng lúc"
    #   env_var: "MAX_BOOKS"
    #   min: 1
    #   max: 50
    #   hot_reload: true

# REFERENCED BY — API/domain nào dùng config này
referenced_by: []                 # Danh sách doc names (api_*, domain_*, lifecycle_*...)

# ENVIRONMENT OVERRIDES — Giá trị khác theo môi trường
environment_overrides:
  development: {}                 # Override cho dev
  staging: {}                     # Override cho staging
  production: {}                  # Override cho production
  # Ví dụ:
  # development:
  #   max_books_per_user: 100     # Dev cho mượn nhiều để test
  # production:
  #   max_books_per_user: 5

# MULTI-TENANT (optional)
tenant_overridable: []            # Danh sách keys mà tenant có thể override
  # Ví dụ: tenant_overridable: ["max_books_per_user", "borrow_duration_days"]
```

### 4.3. Ví dụ: `config_borrowing.yaml`

```yaml
config: borrowing
description: "Cấu hình cho module mượn/trả sách"
scope: per-tenant

values:
  max_books_per_user:
    type: integer
    default: 5
    description: "Số sách tối đa mỗi user được mượn cùng lúc"
    env_var: "MAX_BOOKS"
    min: 1
    max: 50
    hot_reload: true
  borrow_duration_days:
    type: integer
    default: 14
    description: "Thời hạn mượn sách (ngày)"
    env_var: "BORROW_DURATION"
    min: 1
    max: 90
    hot_reload: true
  overdue_penalty_per_day:
    type: number
    default: 0.5
    description: "Phí phạt quá hạn mỗi ngày (USD)"
    min: 0
    hot_reload: true
  auto_suspend_after_days:
    type: integer
    default: 30
    description: "Tự động khóa tài khoản sau N ngày quá hạn"
    min: 7
    max: 365
    hot_reload: false
  reservation_timeout_hours:
    type: integer
    default: 24
    description: "Thời gian giữ sách đặt trước (giờ)"
    min: 1
    max: 72
    hot_reload: true

referenced_by:
  - api_borrow-book_v1
  - api_reserve-book_v1
  - api_check-overdue_v1
  - domain_user
  - lifecycle_book

environment_overrides:
  development:
    max_books_per_user: 100
    borrow_duration_days: 1
    overdue_penalty_per_day: 0
  staging:
    max_books_per_user: 10
  production:
    max_books_per_user: 5

tenant_overridable:
  - max_books_per_user
  - borrow_duration_days
  - overdue_penalty_per_day
```

---

## 5. Enhanced Observability — Quan sát nâng cao

### 5.1. Tại sao cần nâng cấp

Observability hiện tại:
```yaml
observability:
  metrics: ["latency"]
```

👉 **Thiếu business metrics** — chỉ biết "API nhanh hay chậm", không biết "hệ thống hoạt động hiệu quả không"

### 5.2. Observability v2 — Template

```yaml
# Thay thế / mở rộng section observability: trong api_*.yaml
observability:
  # === GIỮ NGUYÊN TỪ V1 ===
  logging_level: info             # debug | info | warn | error
  trace_propagation: true

  # === NÂNG CẤP: TECHNICAL METRICS ===
  technical_metrics:
    - name: ""                    # Tên metric
      type: ""                    # counter | gauge | histogram
      description: ""
      alert_threshold: ""         # Ngưỡng cảnh báo
      # Ví dụ:
      # - name: api_call_count
      #   type: counter
      #   description: "Tổng số lần gọi API"
      # - name: api_latency_ms
      #   type: histogram
      #   buckets: [50, 100, 200, 500, 1000, 5000]
      #   alert_threshold: "p99 > 3000ms"

  # === MỚI: BUSINESS METRICS ===
  business_metrics:
    - name: ""                    # Tên metric nghiệp vụ
      type: ""                    # counter | gauge | rate
      description: ""
      unit: ""                    # books | users | transactions | currency
      alert_threshold: ""
      dashboard: ""               # Dashboard nào hiển thị metric này
      # Ví dụ:
      # - name: books_borrowed_per_day
      #   type: counter
      #   description: "Số sách được mượn mỗi ngày"
      #   unit: books
      #   dashboard: "lending-overview"
      # - name: failed_borrow_rate
      #   type: gauge
      #   description: "Tỉ lệ mượn sách thất bại"
      #   alert_threshold: "> 5%"

  # === MỚI: DISTRIBUTED TRACING ===
  tracing:
    span_name: ""                 # Tên span cho tracing
    parent_span: ""               # Span cha (nếu có)
    attributes: {}                # Custom attributes cho span
    # Ví dụ:
    # span_name: "borrow-book"
    # parent_span: "user-session"
    # attributes:
    #   book_category: "response.book.category"
    #   user_tier: "context.user.membership_tier"

  # === MỚI: RUNTIME FEEDBACK LOOP ===
  # Khi metric vượt ngưỡng → gợi ý update docs
  feedback_triggers:
    - metric: ""                  # Metric nào trigger
      condition: ""               # Điều kiện
      action: ""                  # Hành động gợi ý
      # Ví dụ:
      # - metric: api_error_rate
      #   condition: "> 10% for 1 hour"
      #   action: "review_error_schema — có thể thiếu error case trong docs"
      # - metric: api_latency_p99
      #   condition: "> 5000ms for 30 minutes"
      #   action: "update_performance_section — latency thực tế cao hơn docs claim"
```

---

## 6. Enhanced Tier Detection — Phát hiện Tier chính xác hơn

### 6.1. Vấn đề hiện tại

Tier detection dựa trên số lượng (endpoint, LOC...) → **không phản ánh complexity thực sự**:
- 3 endpoint AI pipeline = Tier 3 complexity
- 20 endpoint CRUD = Tier 2 complexity

### 6.2. Complexity Signals bổ sung

Bảng bổ sung vào **Section 1.2 của SKILL.md**:

| Tín hiệu phức tạp | Cách phát hiện | Điểm |
|---|---|---|
| AI/ML pipeline | Import tensorflow, torch, openai... | +8 |
| Complex state machine (>5 states) | Phát hiện enum states, FSM pattern | +5 |
| Event-driven architecture | Event emitter, RabbitMQ, Kafka imports | +4 |
| Multi-tenant | Tenant context, schema isolation | +5 |
| Real-time / WebSocket | ws, socket.io imports | +3 |
| CRUD-only pattern (giảm điểm) | Chỉ có basic CRUD, không có business logic | -2 /endpoint |
| External API integrations (>3) | Nhiều HTTP client calls | +3 |
| Complex auth (ABAC, policies) | Policy engine, attribute checks | +3 |
| Background job processing | BullMQ, Agenda, node-cron | +3 |
| File/media processing | Multer, sharp, ffmpeg | +2 |

### 6.3. Quy tắc tính điểm cập nhật

```
Tổng = Base signals (Section 1.2 cũ) + Complexity signals (mới)

Tổng điểm 1-7    → Tier 1: Starter
Tổng điểm 8-20   → Tier 2: Standard
Tổng điểm 21+    → Tier 3: Enterprise

⚠️ OVERRIDE RULE:
- Nếu có BẤT KỲ signal nào +5 trở lên → tối thiểu Tier 2
- Nếu có ≥ 2 signals +5 trở lên → tối thiểu Tier 3
```

---

## 7. Blueprint Enforcement — Ép chuyển trạng thái

### 7.1. Vấn đề

Blueprint docs có thể tồn tại mãi mãi ở trạng thái "blueprint" → tạo "docs ảo".

### 7.2. Cơ chế enforcement

```yaml
# Thêm vào blueprint_tracking trong api template
blueprint_tracking:
  # ... fields cũ giữ nguyên ...

  # MỚI: Enforcement
  enforcement:
    max_age_days: 30              # Sau N ngày → cảnh báo
    auto_deprecate_days: 90       # Sau N ngày → tự đánh dấu deprecated
    review_reminder: true         # Gửi reminder khi sắp hết hạn
    # Khi skill chạy incremental scan:
    # - blueprint age > max_age_days → WARNING trong report
    # - blueprint age > auto_deprecate_days → đổi status: deprecated + cảnh báo
```

---

## 8. Runtime Feedback Loop — Vòng phản hồi tự động

### 8.1. Concept

```
Luồng hiện tại (một chiều):
code → docs

Luồng nâng cấp (hai chiều):
code → docs
runtime → observability → feedback_triggers → update docs
```

### 8.2. Implementation

Thêm section mới vào SKILL.md — Processing Engine:

```
Bước 8 (MỚI): Runtime Feedback Check
1. Nếu dự án có monitoring/observability data accessible:
   - Đọc error rate thực tế → so sánh với error schema trong docs
   - Đọc latency thực tế → so sánh với performance.expected_latency_ms
   - Đọc top errors → kiểm tra có trong errors[] không
2. Nếu phát hiện drift:
   - API hay fail với error code không có trong docs → gợi ý thêm error case
   - Latency thực tế >> expected → gợi ý update performance section
   - API bị deprecated trên runtime nhưng docs chưa mark → gợi ý deprecate
3. Output: Runtime Feedback Report (kèm theo Validation Report)
```
