# Domain Modeling — Mô hình nghiệp vụ, Vòng đời, Sự kiện

> File này chứa templates và hướng dẫn cho 3 loại doc mới:
> **Domain Model**, **Lifecycle (State Machine)**, **Event System**.
> Tham chiếu từ `SKILL.md` chính.

---

## 1. Domain Model — Luật nghiệp vụ thật sự

### 1.1. Khi nào tạo

- Có entity/aggregate phức tạp (không chỉ là CRUD)
- Có invariant (quy tắc bất biến) cần enforce
- Nhiều API cùng thao tác trên 1 entity → cần "nguồn sự thật" cho business rules
- Agent cần hiểu **tại sao** hệ thống cho phép/từ chối 1 hành động

> 💡 `domain_*.yaml` khác với `schema_*.md`:
> - `schema_` = cấu trúc database (cột, kiểu dữ liệu, index)
> - `domain_` = luật chơi kinh doanh (invariant, aggregate, business rules)

### 1.2. Template `domain_{entity}.yaml`

```yaml
# File: domain_{entity}.yaml
# Mô hình nghiệp vụ cho entity — KHÔNG phải schema database

# IDENTITY
entity: ""                        # Tên entity (PascalCase)
description: ""                   # Mô tả ngắn gọn vai trò trong hệ thống
bounded_context: ""               # Domain context (ví dụ: "lending", "inventory")

# INVARIANTS — Luật bất biến (QUAN TRỌNG NHẤT)
# Agent PHẢI kiểm tra invariant trước khi gọi API thay đổi state
invariants:
  - rule: ""                      # Mô tả luật bằng ngôn ngữ tự nhiên
    enforced_by: ""               # API hoặc layer nào enforce (ví dụ: "api_borrow-book_v1")
    violation_error: ""            # Error code khi vi phạm
    severity: "block"             # block = chặn hành động | warn = cảnh báo
  # Thêm invariant khác...

# AGGREGATE — Cấu trúc nhóm entity
aggregate:
  root: ""                        # Entity gốc (thường là entity này)
  children: []                    # Các entity con thuộc aggregate
  consistency: "strong"           # strong | eventual — cách đảm bảo tính nhất quán

# RELATIONSHIPS — Quan hệ với entity khác
relationships:
  - target: ""                    # Tên entity liên quan
    type: ""                      # one-to-one | one-to-many | many-to-many
    cascade: ""                   # restrict | cascade | set-null — khi xóa
    description: ""               # Mô tả quan hệ

# BUSINESS RULES — Quy tắc nghiệp vụ bổ sung (không phải invariant)
business_rules:
  - name: ""                      # Tên quy tắc
    description: ""               # Mô tả chi tiết
    applies_to: []                # Danh sách API bị ảnh hưởng
    configurable: false           # Có thể thay đổi runtime không

# VALUE OBJECTS — Các đối tượng giá trị thuộc entity
value_objects:
  - name: ""                      # Ví dụ: "EmailAddress", "Money"
    type: ""
    constraints: ""               # Regex, range, enum...

# DOMAIN EVENTS — Sự kiện entity này phát ra
emits_events: []                  # Danh sách event names (tham chiếu event_*.yaml)

# RELATED APIs — Các API thao tác trên entity này
related_apis: []                  # Danh sách API names (tham chiếu api_*.yaml)
```

### 1.3. Template `domain_{entity}.md`

```markdown
# Domain: [Entity Name]

> **Schema file:** [`domain_{entity}.yaml`](./domain_{entity}.yaml)
> **Bounded Context:** [context] | **Aggregate Root:** [yes/no]

## Mô tả nghiệp vụ

> **WHY**: [Tại sao entity này tồn tại trong hệ thống, giải quyết bài toán gì]

[Mô tả vai trò và ý nghĩa kinh doanh]

## Invariants (Luật bất biến)

| # | Quy tắc | Enforced bởi | Khi vi phạm |
|---|---------|-------------|-------------|
| 1 | [Luật] | [API/layer] | [Error code] |

> ⚠️ **Agent PHẢI kiểm tra invariants trước khi thực hiện hành động thay đổi state.**

## Aggregate Structure

```
[Root Entity]
├── [Child Entity 1]
└── [Child Entity 2]
```

## Relationships

| Entity liên quan | Kiểu quan hệ | Cascade | Mô tả |
|-----------------|--------------|---------|-------|
| | | | |

## Business Rules

| Quy tắc | Mô tả | Áp dụng cho | Cấu hình được? |
|---------|--------|-------------|----------------|
| | | | |

## Domain Events

| Event | Khi nào phát | Consumers |
|-------|-------------|-----------|
| | | |

## APIs liên quan

| API | Hành động | Invariants liên quan |
|-----|-----------|---------------------|
| | | |
```

### 1.4. Ví dụ đầy đủ: `domain_user.yaml`

```yaml
entity: User
description: "Người dùng trong hệ thống thư viện — có thể mượn/trả sách"
bounded_context: "user-management"

invariants:
  - rule: "Email phải unique trong toàn hệ thống"
    enforced_by: "database unique constraint + api_create-user_v1"
    violation_error: "EMAIL_ALREADY_EXISTS"
    severity: block
  - rule: "Không thể xóa user nếu có giao dịch mượn đang active"
    enforced_by: "api_delete-user_v1 (pre-check)"
    violation_error: "USER_HAS_ACTIVE_LOANS"
    severity: block
  - rule: "Mỗi user tối đa mượn N sách cùng lúc (N = config)"
    enforced_by: "api_borrow-book_v1 (pre-check)"
    violation_error: "BORROW_LIMIT_EXCEEDED"
    severity: block

aggregate:
  root: User
  children: [UserProfile, UserPreferences, MembershipCard]
  consistency: strong

relationships:
  - target: BorrowTransaction
    type: one-to-many
    cascade: restrict
    description: "User có nhiều giao dịch mượn sách"
  - target: MembershipCard
    type: one-to-one
    cascade: cascade
    description: "Mỗi user có 1 thẻ thành viên"

business_rules:
  - name: "Auto-suspend overdue users"
    description: "User quá hạn trả sách >30 ngày sẽ bị tạm khóa tài khoản"
    applies_to: ["api_check-overdue_v1", "cron_daily-overdue-check"]
    configurable: true

value_objects:
  - name: EmailAddress
    type: string
    constraints: "RFC 5322 compliant email"
  - name: MembershipTier
    type: string
    constraints: "enum: [basic, silver, gold, platinum]"

emits_events:
  - user_created
  - user_updated
  - user_suspended
  - user_deleted

related_apis:
  - api_create-user_v1
  - api_get-user_v1
  - api_update-user_v1
  - api_delete-user_v1
```

---

## 2. Lifecycle — Máy trạng thái (State Machine)

### 2.1. Khi nào tạo

- Entity có nhiều trạng thái rõ ràng (≥3 states)
- Có quy tắc chuyển trạng thái (không phải bất kỳ state nào cũng chuyển qua state nào)
- Agent cần biết "API này có được gọi ở trạng thái hiện tại không?"
- Có timeout / auto-transition

### 2.2. Template `lifecycle_{entity}.yaml`

```yaml
# File: lifecycle_{entity}.yaml
# Mô hình vòng đời / máy trạng thái cho entity

# IDENTITY
entity: ""                        # Tên entity (phải khớp với domain_*.yaml nếu có)
description: ""                   # Mô tả ngắn về vòng đời
initial_state: ""                 # Trạng thái khởi tạo

# STATES — Danh sách trạng thái
states:
  - name: ""                      # Tên trạng thái (snake_case)
    description: ""               # Mô tả
    is_terminal: false            # true = trạng thái kết thúc (không chuyển tiếp được)
    ui_label: ""                  # Label hiển thị trên UI (cho frontend)
    ui_color: ""                  # Màu sắc gợi ý (ví dụ: "green", "#28a745")

# TRANSITIONS — Quy tắc chuyển trạng thái
transitions:
  - from: ""                      # Trạng thái nguồn
    to: ""                        # Trạng thái đích
    via: ""                       # API/action kích hoạt (tham chiếu api_*.yaml)
    guard: ""                     # Điều kiện phải đúng (precondition)
    side_effects: []              # Hành động kèm theo khi chuyển
    emits_event: ""               # Event phát ra khi chuyển (tham chiếu event_*.yaml)

# AUTO TRANSITIONS — Chuyển tự động theo thời gian/điều kiện
auto_transitions:
  - from: ""                      # Trạng thái nguồn
    to: ""                        # Trạng thái đích
    trigger: ""                   # "timeout:24h" | "cron:daily" | "condition:..."
    description: ""               # Mô tả lý do auto-transition

# STATE INVARIANTS — Ràng buộc theo trạng thái
# Mỗi state có thể có invariant riêng
state_invariants:
  state_name:
    - rule: ""
      enforced_by: ""
```

### 2.3. Template `lifecycle_{entity}.md`

```markdown
# Lifecycle: [Entity Name]

> **Schema file:** [`lifecycle_{entity}.yaml`](./lifecycle_{entity}.yaml)
> **Initial State:** [state] | **Terminal States:** [states]

## Sơ đồ vòng đời

```
[State A] ──(action)-→ [State B] ──(action)-→ [State C]
     │                                           │
     └──────────(timeout)─────────────────────────┘
```

## Các trạng thái

| State | Mô tả | Terminal? | UI Label | UI Color |
|-------|--------|----------|----------|----------|
| | | | | |

## Chuyển trạng thái (Transitions)

| Từ | Đến | Kích hoạt bởi | Điều kiện | Event phát ra |
|----|-----|--------------|-----------|---------------|
| | | | | |

## Auto Transitions

| Từ | Đến | Trigger | Mô tả |
|----|-----|---------|-------|
| | | | |

## Lưu ý cho Agent

> ⚠️ Agent PHẢI kiểm tra trạng thái hiện tại của entity trước khi gọi API chuyển trạng thái.
> Nếu entity đang ở state không hợp lệ cho transition → KHÔNG gọi API, trả lỗi ngay.
```

### 2.4. Ví dụ đầy đủ: `lifecycle_book.yaml`

```yaml
entity: Book
description: "Vòng đời của sách trong hệ thống thư viện"
initial_state: available

states:
  - name: available
    description: "Sách có sẵn trên kệ, có thể mượn"
    is_terminal: false
    ui_label: "Có sẵn"
    ui_color: "#28a745"
  - name: reserved
    description: "Đã được đặt trước, chờ lấy"
    is_terminal: false
    ui_label: "Đã đặt"
    ui_color: "#ffc107"
  - name: borrowed
    description: "Đang được mượn"
    is_terminal: false
    ui_label: "Đang mượn"
    ui_color: "#dc3545"
  - name: returned
    description: "Đã trả, đang kiểm tra tình trạng"
    is_terminal: false
    ui_label: "Đã trả"
    ui_color: "#17a2b8"
  - name: archived
    description: "Đã ngừng lưu hành"
    is_terminal: true
    ui_label: "Ngừng lưu hành"
    ui_color: "#6c757d"

transitions:
  - from: available
    to: reserved
    via: api_reserve-book_v1
    guard: "user.active_loans < config.max_books_per_user"
    side_effects: ["lock book for 24h"]
    emits_event: book_reserved
  - from: available
    to: borrowed
    via: api_borrow-book_v1
    guard: "user.status == 'active' AND user.active_loans < config.max_books_per_user"
    side_effects: ["update inventory count", "create transaction record"]
    emits_event: book_borrowed
  - from: reserved
    to: borrowed
    via: api_borrow-book_v1
    guard: "reservation.user_id == current_user.id"
    side_effects: ["cancel reservation timer", "create transaction"]
    emits_event: book_borrowed
  - from: reserved
    to: available
    via: api_cancel-reservation_v1
    guard: "reservation.user_id == current_user.id OR user.role == 'admin'"
    emits_event: reservation_cancelled
  - from: borrowed
    to: returned
    via: api_return-book_v1
    guard: ""
    side_effects: ["close transaction", "calculate overdue fee if any"]
    emits_event: book_returned
  - from: returned
    to: available
    via: api_approve-return_v1
    guard: "user.role in ['librarian', 'admin']"
    side_effects: ["update inventory count"]
    emits_event: book_available
  - from: returned
    to: archived
    via: api_archive-book_v1
    guard: "user.role == 'admin' AND book.condition == 'damaged'"
    emits_event: book_archived

auto_transitions:
  - from: reserved
    to: available
    trigger: "timeout:24h"
    description: "Nếu không lấy sách trong 24h, tự động hủy đặt trước"

state_invariants:
  borrowed:
    - rule: "Phải có transaction record active"
      enforced_by: "api_borrow-book_v1"
  reserved:
    - rule: "Chỉ 1 user được reserve cùng lúc"
      enforced_by: "api_reserve-book_v1"
```

---

## 3. Event System — Hệ thống sự kiện

### 3.1. Khi nào tạo

- Hệ thống có async processing (queue, worker)
- Nhiều service cần react khi 1 hành động xảy ra
- Cần audit trail / event sourcing
- Agent cần biết "khi API này chạy xong, chuyện gì xảy ra tiếp?"
- Chuẩn bị scale sang microservices

### 3.2. Template `event_{name}.yaml`

```yaml
# File: event_{name}.yaml
# Định nghĩa sự kiện trong hệ thống

# IDENTITY
event: ""                         # Tên event (snake_case)
description: ""                   # Mô tả sự kiện
domain: ""                        # Bounded context (ví dụ: "lending", "inventory")
severity: "info"                  # info | warning | critical

# TRIGGER — Nguồn phát sự kiện
triggered_by: ""                  # API/action phát ra event (tham chiếu api_*.yaml)
trigger_condition: ""             # Điều kiện để event được phát (nếu có)

# PAYLOAD — Dữ liệu kèm theo event
payload:
  type: object
  required: []
  properties: {}
  # Ví dụ:
  # book_id: { type: string, format: uuid }
  # user_id: { type: string, format: uuid }

# CONSUMERS — Ai/cái gì lắng nghe event này
consumers:
  - name: ""                      # Tên consumer/handler
    action: ""                    # Hành động thực hiện
    async: true                   # true = xử lý bất đồng bộ
    required: true                # true = bắt buộc xử lý | false = optional
    failure_strategy: ""          # retry | skip | dead-letter
    max_retries: 3
  # Thêm consumer khác...

# DELIVERY — Cách truyền tải event
delivery:
  channel: ""                     # "internal" | "rabbitmq" | "kafka" | "redis-pubsub"
  topic: ""                       # Topic/queue name
  ordering: false                 # Có cần đảm bảo thứ tự không
  idempotent: true                # Consumer phải handle duplicate không

# RELATED
related_events: []                # Event liên quan (ví dụ: book_borrowed → book_returned)
related_lifecycle: ""             # Lifecycle mà event thuộc về (tham chiếu lifecycle_*.yaml)
```

### 3.3. Template `event_{name}.md`

```markdown
# Event: [event_name]

> **Schema file:** [`event_{name}.yaml`](./event_{name}.yaml)
> **Domain:** [context] | **Severity:** [level]

## Mô tả

[Khi nào sự kiện này xảy ra và ý nghĩa của nó]

## Trigger

- **Phát bởi:** [`api_name`](./api_name.yaml)
- **Điều kiện:** [điều kiện nếu có]

## Payload

| Field | Kiểu | Bắt buộc | Mô tả |
|-------|------|----------|-------|
| | | | |

## Consumers

| Consumer | Hành động | Async | Bắt buộc | Khi fail |
|----------|----------|-------|----------|---------|
| | | | | |

## Luồng xử lý

```
[API gọi] → event phát ra → [Consumer 1] → [Side effect 1]
                            → [Consumer 2] → [Side effect 2]
```

## Lưu ý

- [Ordering requirements]
- [Idempotency notes]
- [Failure handling]
```

### 3.4. Ví dụ đầy đủ: `event_book-borrowed.yaml`

```yaml
event: book_borrowed
description: "Phát ra khi user mượn sách thành công"
domain: "lending"
severity: info

triggered_by: api_borrow-book_v1
trigger_condition: "API trả về HTTP 200 (mượn thành công)"

payload:
  type: object
  required: [book_id, user_id, transaction_id, borrowed_at, due_date]
  properties:
    book_id:
      type: string
      format: uuid
      description: "ID sách vừa được mượn"
    user_id:
      type: string
      format: uuid
      description: "ID user mượn sách"
    transaction_id:
      type: string
      format: uuid
      description: "ID giao dịch mượn"
    borrowed_at:
      type: string
      format: date-time
      description: "Thời điểm mượn"
    due_date:
      type: string
      format: date-time
      description: "Hạn trả sách"

consumers:
  - name: update_inventory
    action: "Giảm số lượng sách available trong kho"
    async: false
    required: true
    failure_strategy: retry
    max_retries: 3
  - name: send_borrow_confirmation
    action: "Gửi email xác nhận cho user"
    async: true
    required: false
    failure_strategy: dead-letter
    max_retries: 5
  - name: schedule_due_reminder
    action: "Đặt lịch nhắc nhở trả sách trước 3 ngày"
    async: true
    required: false
    failure_strategy: retry
    max_retries: 3
  - name: update_user_stats
    action: "Cập nhật thống kê mượn sách của user"
    async: true
    required: false
    failure_strategy: skip

delivery:
  channel: "internal"
  topic: "lending.book_borrowed"
  ordering: false
  idempotent: true

related_events:
  - book_returned
  - book_overdue
related_lifecycle: lifecycle_book
```

---

## 4. Data Flow — Luồng dữ liệu

### 4.1. Khi nào tạo

- Dữ liệu đi qua nhiều bước xử lý (>3 steps)
- Cần trace "dữ liệu này đến từ đâu?"
- Agent cần hiểu pipeline end-to-end

### 4.2. Template `dataflow_{feature}.md`

```markdown
# Data Flow: [Feature Name]

## Tổng quan

[Mô tả ngắn luồng dữ liệu]

## Sơ đồ luồng

```
[Input Source]
    │
    ▼
[Step 1: API/Action] → [Side Effect]
    │
    ▼
[Step 2: Processing] → [Side Effect]
    │
    ▼
[Step 3: Output/Storage]
```

## Chi tiết từng bước

| Bước | API/Action | Input | Output | Side Effects |
|------|-----------|-------|--------|-------------|
| 1 | | | | |
| 2 | | | | |

## Data Transformations

| Từ | Đến | Transformation |
|----|-----|---------------|
| | | |

## Error Points

| Bước | Lỗi có thể | Xử lý |
|------|-----------|-------|
| | | |
```

---

## 5. Quy tắc sử dụng chung

### 5.1. Quan hệ giữa các doc types

```
domain_{entity}.yaml    ← Luật chơi kinh doanh
    │
    ├── lifecycle_{entity}.yaml   ← Vòng đời entity
    │       │
    │       └── event_{name}.yaml ← Sự kiện khi chuyển state
    │
    ├── api_{action}_v1.yaml      ← API thao tác trên entity
    │
    └── schema_{table}.md         ← Cấu trúc lưu trữ database
```

### 5.2. Agent phải đọc theo thứ tự

1. **`_registry.yaml`** → biết có gì
2. **`domain_*.yaml`** → hiểu luật chơi
3. **`lifecycle_*.yaml`** → hiểu trạng thái cho phép
4. **`api_*.yaml`** → biết cách gọi
5. **`event_*.yaml`** → biết chuyện gì xảy ra sau

### 5.3. Cross-reference rules

- `domain_*.yaml` → `related_apis` phải trỏ đúng tên api docs
- `lifecycle_*.yaml` → `via` trong transitions phải trỏ đúng tên api docs
- `lifecycle_*.yaml` → `emits_event` phải trỏ đúng tên event docs
- `event_*.yaml` → `triggered_by` phải trỏ đúng tên api docs
- `event_*.yaml` → `related_lifecycle` phải trỏ đúng tên lifecycle docs
